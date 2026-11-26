import base64
import logging
from typing import Optional

from app.schemas.voice import (
    MOCK_STT_DISCLAIMER,
    MOCK_TRANSLATION_DISCLAIMER,
    MOCK_TTS_DISCLAIMER,
    SUPPORTED_LANGUAGE_CODES,
)
from app.services.voice.adapters.base import (
    BaseSTTAdapter,
    BaseTranslationAdapter,
    BaseTTSAdapter,
    STTResult,
    TranslationResult,
    TTSResult,
)
from app.services.voice.emergency_dictionary import (
    DRAFT_EMERGENCY_DICTIONARY,
    get_draft_emergency_phrase,
)

logger = logging.getLogger("pulseguardian.voice.mock")

MOCK_PROVIDER_NAME = "mock_development"


class MockSTTAdapter(BaseSTTAdapter):
    """
    Development Mock STT Adapter.
    Explicitly identifies as a mock and never pretends to run machine learning
    or speech recognition on raw audio bytes.
    """

    def transcribe(
        self,
        audio_bytes: bytes,
        content_type: str = "audio/wav",
        hint_language: Optional[str] = None
    ) -> STTResult:
        lang = hint_language.lower() if hint_language else "en"
        if lang not in SUPPORTED_LANGUAGE_CODES:
            lang = "en"

        audio_len = len(audio_bytes) if audio_bytes else 0

        # Non-deceptive simulated output clearly stating it is a mock placeholder
        simulated_transcript = (
            f"[Simulated Audio Transcription ({lang.upper()})]: "
            f"Mock audio payload received ({audio_len} bytes, type: {content_type}). "
            f"No acoustic speech model was executed."
        )

        return STTResult(
            transcript=simulated_transcript,
            detected_language=lang,
            confidence=0.85,
            provider=MOCK_PROVIDER_NAME,
            is_mock=True,
            disclaimer=MOCK_STT_DISCLAIMER,
            uncertain_speech=False
        )


class MockTranslationAdapter(BaseTranslationAdapter):
    """
    Development Mock Translation Adapter.
    Explicitly identifies as a mock and does not claim to produce certified translations.
    """

    def translate(
        self,
        text: str,
        source_language: Optional[str],
        target_language: str
    ) -> TranslationResult:
        src = source_language.lower() if source_language else "en"
        tgt = target_language.lower()

        # Check if text corresponds to a known draft phrase key
        for key, lang_map in DRAFT_EMERGENCY_DICTIONARY.items():
            for l_code, phrase in lang_map.items():
                if text.strip() == phrase.strip():
                    translated_val = get_draft_emergency_phrase(key, tgt)
                    return TranslationResult(
                        original_text=text,
                        translated_text=f"[Draft Reference {tgt.upper()}]: {translated_val}",
                        source_language=src,
                        target_language=tgt,
                        confidence=None,
                        provider=MOCK_PROVIDER_NAME,
                        is_mock=True,
                        disclaimer=MOCK_TRANSLATION_DISCLAIMER,
                        uncertain_translation=False
                    )

        # Standard simulated translation pattern
        simulated_translation = f"[Simulated {tgt.upper()} Translation]: {text}"

        return TranslationResult(
            original_text=text,
            translated_text=simulated_translation,
            source_language=src,
            target_language=tgt,
            confidence=None,
            provider=MOCK_PROVIDER_NAME,
            is_mock=True,
            disclaimer=MOCK_TRANSLATION_DISCLAIMER,
            uncertain_translation=False
        )


class MockTTSAdapter(BaseTTSAdapter):
    """
    Development Mock TTS Adapter.
    Generates non-playable simulated audio byte markers. Explicitly marks is_playable=False.
    """

    def synthesize(
        self,
        text: str,
        language_code: str,
        voice_gender: str = "neutral",
        audio_format: str = "audio/mock-synthesized",
    ) -> TTSResult:
        lang = language_code.lower()

        # Deterministic mock byte buffer (ASCII header)
        mock_raw_bytes = f"MOCK_TTS_AUDIO_BUFFER_{lang.upper()}_{text[:30]}".encode("utf-8")
        mock_b64 = base64.b64encode(mock_raw_bytes).decode("utf-8")

        # If caller passed a standard MIME format, we can report it or keep mock-synthesized
        output_format = audio_format if audio_format != "audio/mp3" else "audio/mock-synthesized"

        return TTSResult(
            language_code=lang,
            audio_payload=mock_b64,
            audio_format=output_format,
            is_mock=True,
            is_playable=False,
            provider=MOCK_PROVIDER_NAME,
            disclaimer=MOCK_TTS_DISCLAIMER
        )
