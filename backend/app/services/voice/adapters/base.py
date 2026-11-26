from abc import ABC, abstractmethod
from typing import NamedTuple, Optional


class STTResult(NamedTuple):
    transcript: str
    detected_language: str
    confidence: Optional[float]  # None if uncalibrated or unavailable
    provider: str
    is_mock: bool
    disclaimer: str
    uncertain_speech: bool = False


class TranslationResult(NamedTuple):
    original_text: str
    translated_text: str
    source_language: str
    target_language: str
    confidence: Optional[float]  # None if uncalibrated or unavailable
    provider: str
    is_mock: bool
    disclaimer: str
    uncertain_translation: bool = False


class TTSResult(NamedTuple):
    language_code: str
    audio_payload: str
    audio_format: str
    is_mock: bool
    is_playable: bool
    provider: str
    disclaimer: str


class BaseSTTAdapter(ABC):
    """Abstract interface for Speech-to-Text transcription and language detection."""

    @abstractmethod
    def transcribe(
        self,
        audio_bytes: bytes,
        content_type: str = "audio/wav",
        hint_language: Optional[str] = None
    ) -> STTResult:
        """Transcribes audio payload and detects spoken language."""
        pass


class BaseTranslationAdapter(ABC):
    """Abstract interface for Multilingual Text Translation."""

    @abstractmethod
    def translate(
        self,
        text: str,
        source_language: Optional[str],
        target_language: str
    ) -> TranslationResult:
        """Translates text from source to target language."""
        pass


class BaseTTSAdapter(ABC):
    """Abstract interface for Text-to-Speech audio synthesis."""

    @abstractmethod
    def synthesize(
        self,
        text: str,
        language_code: str,
        voice_gender: str = "neutral",
        audio_format: str = "audio/mp3",
    ) -> TTSResult:
        """Synthesizes text into audio bytes/base64."""
        pass
