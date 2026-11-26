import base64
import logging
from typing import Dict, Optional

from app.core.config import settings
from app.schemas.voice import (
    REAL_TTS_DISCLAIMER,
    SUPPORTED_LANGUAGE_CODES,
    SUPPORTED_TTS_AUDIO_FORMATS,
)
from app.services.voice.adapters.base import BaseTTSAdapter, TTSResult

logger = logging.getLogger("pulseguardian.voice.tts")

# Mapping of generic voice gender / role identifiers to OpenAI TTS voice models
OPENAI_VOICE_MAP: Dict[str, str] = {
    "female": "nova",
    "male": "onyx",
    "neutral": "alloy",
    "alloy": "alloy",
    "echo": "echo",
    "fable": "fable",
    "onyx": "onyx",
    "nova": "nova",
    "shimmer": "shimmer",
}

# Mapping of audio MIME types to OpenAI /v1/audio/speech response_format parameters
MIME_TO_OPENAI_FORMAT: Dict[str, str] = {
    "audio/mp3": "mp3",
    "audio/mpeg": "mp3",
    "audio/wav": "wav",
    "audio/x-wav": "wav",
    "audio/ogg": "opus",
    "audio/opus": "opus",
    "audio/aac": "aac",
    "audio/flac": "flac",
}


class HostedOpenAITTSAdapter(BaseTTSAdapter):
    """
    Hosted Text-to-Speech (TTS) Adapter using OpenAI Audio Speech API over TLS.
    Synthesizes text for the 7 supported languages (kn, en, hi, ml, ta, te, ur).
    Enforces payload length limits, masks API keys, and never logs audio bytes or patient text.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        model_name: Optional[str] = None,
        timeout_seconds: float = 30.0,
    ):
        self.api_key = api_key if api_key is not None else (settings.TTS_API_KEY or settings.OPENAI_API_KEY)
        self.api_base = api_base or settings.TTS_API_BASE
        self.model_name = model_name or settings.TTS_MODEL_NAME
        self.timeout_seconds = timeout_seconds

    def synthesize(
        self,
        text: str,
        language_code: str,
        voice_gender: str = "neutral",
        audio_format: str = "audio/mp3",
    ) -> TTSResult:
        """
        Synthesizes text into acoustic speech audio via hosted TLS endpoint.
        Returns a TTSResult with base64-encoded audio payload and is_playable=True.
        """
        if not text or not text.strip():
            raise ValueError("Text to synthesize cannot be empty.")

        cleaned_text = text.strip()
        if len(cleaned_text) > settings.VOICE_MAX_TTS_CHARS:
            raise ValueError(
                f"TTS text length ({len(cleaned_text)} chars) exceeds maximum limit of "
                f"{settings.VOICE_MAX_TTS_CHARS} characters."
            )

        if not self.api_key or not self.api_key.strip():
            raise RuntimeError(
                "TTS_API_KEY (or OPENAI_API_KEY) is not configured for hosted TTS."
            )

        lang = language_code.lower().strip()
        if lang not in SUPPORTED_LANGUAGE_CODES:
            raise ValueError(
                f"Unsupported language code '{language_code}'. Supported: {', '.join(SUPPORTED_LANGUAGE_CODES)}"
            )

        # Voice gender / voice name mapping
        voice_key = (voice_gender or "neutral").lower().strip()
        if voice_key not in OPENAI_VOICE_MAP:
            valid_voices = ["neutral", "female", "male"] + list(OPENAI_VOICE_MAP.keys())
            raise ValueError(
                f"Invalid voice identifier '{voice_gender}'. Allowed: {', '.join(sorted(set(valid_voices)))}"
            )
        target_voice = OPENAI_VOICE_MAP[voice_key]

        # Audio MIME container format mapping
        fmt_key = (audio_format or "audio/mp3").lower().strip()
        if fmt_key not in MIME_TO_OPENAI_FORMAT:
            raise ValueError(
                f"Unsupported audio format '{audio_format}'. Supported formats: {', '.join(SUPPORTED_TTS_AUDIO_FORMATS)}"
            )
        response_format = MIME_TO_OPENAI_FORMAT[fmt_key]

        # Lazy import of httpx
        import httpx

        url = f"{self.api_base.rstrip('/')}/audio/speech"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        data = {
            "model": self.model_name,
            "input": cleaned_text,
            "voice": target_voice,
            "response_format": response_format,
        }

        logger.info(
            f"Dispatching hosted TTS request: language={lang}, format={response_format}, "
            f"voice={target_voice}, char_count={len(cleaned_text)}"
        )

        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.post(url, headers=headers, json=data)
        except httpx.TimeoutException:
            logger.error("Hosted TTS request timed out.")
            raise TimeoutError("Hosted TTS synthesis service timed out.")
        except httpx.RequestError as exc:
            logger.error(f"Hosted TTS network error: {exc.__class__.__name__}")
            raise ConnectionError(f"Network error communicating with TTS provider: {exc.__class__.__name__}")

        if response.status_code == 401:
            raise RuntimeError("Hosted TTS authentication failed: Invalid API credentials.")
        elif response.status_code == 429:
            raise RuntimeError("Hosted TTS rate limit or quota exceeded.")
        elif response.status_code >= 400:
            raise ConnectionError(f"Hosted TTS provider error with status {response.status_code}")

        audio_bytes = response.content
        if not audio_bytes or len(audio_bytes) == 0:
            raise RuntimeError("Received empty audio response from TTS provider.")

        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")

        return TTSResult(
            language_code=lang,
            audio_payload=audio_b64,
            audio_format=fmt_key,
            is_mock=False,
            is_playable=True,
            provider="hosted_tts",
            disclaimer=REAL_TTS_DISCLAIMER,
        )


class LocalTTSAdapter(BaseTTSAdapter):
    """
    Local/Offline Multilingual TTS Adapter (e.g. Piper, eSpeak-NG, or Indic-TTS).
    Lazily initializes the offline speech engine when requested.
    Raises RuntimeError if local synthesis dependencies are missing.
    """

    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path
        self._engine = None

    def _load_engine(self):
        if self._engine is None:
            raise RuntimeError(
                "Local TTS engine dependencies are not installed in the current environment. "
                "Please configure VOICE_TTS_PROVIDER=hosted_tts or VOICE_TTS_PROVIDER=mock_development."
            )

    def synthesize(
        self,
        text: str,
        language_code: str,
        voice_gender: str = "neutral",
        audio_format: str = "audio/mp3",
    ) -> TTSResult:
        if not text or not text.strip():
            raise ValueError("Text to synthesize cannot be empty.")

        lang = language_code.lower().strip()
        if lang not in SUPPORTED_LANGUAGE_CODES:
            raise ValueError(
                f"Unsupported language code '{language_code}'. Supported: {', '.join(SUPPORTED_LANGUAGE_CODES)}"
            )

        self._load_engine()

        # Offline engine synthesis would be called here if installed
        raise NotImplementedError("Local offline TTS synthesis is not currently configured.")
