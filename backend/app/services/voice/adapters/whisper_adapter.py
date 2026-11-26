import io
import logging
from typing import Optional

from app.core.config import settings
from app.schemas.voice import (
    REAL_STT_DISCLAIMER,
    SUPPORTED_AUDIO_MIME_TYPES,
    SUPPORTED_LANGUAGE_CODES,
)
from app.services.voice.adapters.base import BaseSTTAdapter, STTResult

logger = logging.getLogger("pulseguardian.voice.whisper")


class FasterWhisperSTTAdapter(BaseSTTAdapter):
    """
    Local Speech-to-Text adapter using Faster-Whisper (CTranslate2 backend).
    Processes audio completely in ephemeral memory without persisting files to disk.
    Performs spoken language detection across the 7 supported languages (kn, en, hi, ml, ta, te, ur).
    Flags uncalibrated confidence as None and marks uncertain or unsupported speech safely.
    """

    def __init__(
        self,
        model_size: Optional[str] = None,
        device: Optional[str] = None,
        compute_type: Optional[str] = None,
    ):
        self.model_size = model_size or settings.FASTER_WHISPER_MODEL_SIZE
        self.device = device or settings.FASTER_WHISPER_DEVICE
        self.compute_type = compute_type or settings.FASTER_WHISPER_COMPUTE_TYPE
        self._model = None

    def _get_model(self):
        """Lazily imports and instantiates the Faster-Whisper WhisperModel."""
        if self._model is None:
            try:
                from faster_whisper import WhisperModel
            except ImportError as err:
                raise RuntimeError(
                    "faster-whisper is not installed. To run local Whisper STT, install "
                    "'faster-whisper' with appropriate CTranslate2 runtime or set "
                    "VOICE_STT_PROVIDER=mock_development."
                ) from err

            logger.info(
                f"Loading local Faster-Whisper model size='{self.model_size}' "
                f"on device='{self.device}' with compute_type='{self.compute_type}'"
            )
            self._model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type,
            )
        return self._model

    def transcribe(
        self,
        audio_bytes: bytes,
        content_type: str = "audio/wav",
        hint_language: Optional[str] = None,
    ) -> STTResult:
        if not audio_bytes or len(audio_bytes) == 0:
            raise ValueError("Audio payload cannot be empty.")

        model = self._get_model()

        # Ephemeral in-memory audio byte stream
        audio_stream = io.BytesIO(audio_bytes)

        # Apply hint language only if it matches one of the 7 supported languages
        target_hint = None
        if hint_language and hint_language.lower() in SUPPORTED_LANGUAGE_CODES:
            target_hint = hint_language.lower()

        try:
            segments, info = model.transcribe(
                audio_stream,
                language=target_hint,
                beam_size=5,
                vad_filter=True,
            )

            segment_texts = []
            no_speech_probs = []
            for segment in segments:
                segment_texts.append(segment.text)
                if hasattr(segment, "no_speech_prob") and segment.no_speech_prob is not None:
                    no_speech_probs.append(segment.no_speech_prob)

            transcript = " ".join(segment_texts).strip()
        except Exception as exc:
            logger.error(f"Faster-Whisper transcription failed: {exc.__class__.__name__}")
            raise RuntimeError(f"Local speech transcription failed: {exc.__class__.__name__}") from exc

        # Language identification and uncertainty evaluation
        raw_lang = getattr(info, "language", None) or "en"
        lang_prob = getattr(info, "language_probability", 1.0) or 0.0

        detected_lang = raw_lang.lower()
        uncertain_speech = False

        if detected_lang not in SUPPORTED_LANGUAGE_CODES:
            detected_lang = "unsupported"
            uncertain_speech = True
        elif lang_prob < settings.VOICE_LANGUAGE_CONFIDENCE_THRESHOLD:
            uncertain_speech = True

        if not transcript:
            uncertain_speech = True

        if no_speech_probs and (sum(no_speech_probs) / len(no_speech_probs)) > 0.6:
            uncertain_speech = True

        return STTResult(
            transcript=transcript,
            detected_language=detected_lang,
            confidence=None,  # Uncalibrated confidence represented as None per safety mandate
            provider="local_whisper",
            is_mock=False,
            disclaimer=REAL_STT_DISCLAIMER,
            uncertain_speech=uncertain_speech,
        )


class HostedWhisperSTTAdapter(BaseSTTAdapter):
    """
    Hosted OpenAI Whisper API Speech-to-Text adapter.
    Sends in-memory audio payloads over TLS to the transcription endpoint.
    Performs language detection and maps unsupported languages to 'unsupported' with uncertain_speech=True.
    Masks credentials and avoids exposing API keys in exceptions or logs.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        model_name: str = "whisper-1",
        timeout_seconds: float = 30.0,
    ):
        self.api_key = api_key if api_key is not None else settings.OPENAI_API_KEY
        self.api_base = api_base or settings.OPENAI_API_BASE
        self.model_name = model_name
        self.timeout_seconds = timeout_seconds

    def transcribe(
        self,
        audio_bytes: bytes,
        content_type: str = "audio/wav",
        hint_language: Optional[str] = None,
    ) -> STTResult:
        if not self.api_key or not self.api_key.strip():
            raise RuntimeError(
                "OPENAI_API_KEY is not configured. Set OPENAI_API_KEY in environment or configure "
                "VOICE_STT_PROVIDER=mock_development."
            )

        if not audio_bytes or len(audio_bytes) == 0:
            raise ValueError("Audio payload cannot be empty.")

        # Map MIME type to valid audio filename extension for OpenAI multipart parser
        mime_to_filename = {
            "audio/wav": "audio.wav",
            "audio/x-wav": "audio.wav",
            "audio/mpeg": "audio.mp3",
            "audio/mp3": "audio.mp3",
            "audio/ogg": "audio.ogg",
            "audio/webm": "audio.webm",
            "audio/x-m4a": "audio.m4a",
            "audio/flac": "audio.flac",
        }
        filename = mime_to_filename.get(content_type, "audio.wav")

        data = {
            "model": self.model_name,
            "response_format": "verbose_json",
        }
        if hint_language and hint_language.lower() in SUPPORTED_LANGUAGE_CODES:
            data["language"] = hint_language.lower()

        files = {
            "file": (filename, io.BytesIO(audio_bytes), content_type),
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
        }

        # Lazy import of httpx
        import httpx

        url = f"{self.api_base.rstrip('/')}/audio/transcriptions"

        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.post(url, headers=headers, data=data, files=files)
        except httpx.TimeoutException:
            logger.error("Hosted Whisper request timed out.")
            raise TimeoutError("Hosted Whisper transcription service timed out.")
        except httpx.RequestError as exc:
            logger.error(f"Hosted Whisper network error: {exc.__class__.__name__}")
            raise RuntimeError(f"Network error communicating with Hosted Whisper: {exc.__class__.__name__}")

        if response.status_code == 401:
            raise RuntimeError("Hosted Whisper authentication failed: Invalid API credentials.")
        elif response.status_code == 429:
            raise RuntimeError("Hosted Whisper rate limit or quota exceeded.")
        elif response.status_code >= 400:
            raise ValueError(f"Hosted Whisper rejected audio payload with status {response.status_code}")

        try:
            payload = response.json()
        except Exception as exc:
            raise RuntimeError(f"Invalid JSON response from Hosted Whisper: {exc}")

        transcript = (payload.get("text") or "").strip()
        raw_lang = (payload.get("language") or "en").lower()

        detected_lang = raw_lang
        uncertain_speech = False

        if detected_lang not in SUPPORTED_LANGUAGE_CODES:
            detected_lang = "unsupported"
            uncertain_speech = True

        if not transcript:
            uncertain_speech = True

        return STTResult(
            transcript=transcript,
            detected_language=detected_lang,
            confidence=None,  # Whisper API does not provide a calibrated overall sentence confidence
            provider="hosted_whisper",
            is_mock=False,
            disclaimer=REAL_STT_DISCLAIMER,
            uncertain_speech=uncertain_speech,
        )
