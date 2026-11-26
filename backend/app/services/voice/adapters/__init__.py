from app.core.config import settings
from app.services.voice.adapters.base import (
    BaseSTTAdapter,
    BaseTranslationAdapter,
    BaseTTSAdapter,
    STTResult,
    TranslationResult,
    TTSResult,
)
from app.services.voice.adapters.mock_adapter import (
    MockSTTAdapter,
    MockTranslationAdapter,
    MockTTSAdapter,
)
from app.services.voice.adapters.whisper_adapter import (
    FasterWhisperSTTAdapter,
    HostedWhisperSTTAdapter,
)
from app.services.voice.adapters.translation_adapter import (
    HostedTranslationAdapter,
    IndicTrans2TranslationAdapter,
    detect_script_language,
)
from app.services.voice.adapters.tts_adapter import (
    HostedOpenAITTSAdapter,
    LocalTTSAdapter,
)

# Registry of initialized adapter singletons
_stt_adapter = None
_translation_adapter = None
_tts_adapter = None


def get_stt_adapter() -> BaseSTTAdapter:
    """
    Returns the configured STT adapter based on VOICE_STT_PROVIDER setting:
    - 'local_whisper' / 'faster_whisper': FasterWhisperSTTAdapter
    - 'hosted_whisper' / 'openai_whisper': HostedWhisperSTTAdapter
    - 'mock_development' (or fallback): MockSTTAdapter
    """
    global _stt_adapter
    if _stt_adapter is None:
        provider = (settings.VOICE_STT_PROVIDER or "mock_development").lower().strip()
        if provider in ["local_whisper", "faster_whisper"]:
            _stt_adapter = FasterWhisperSTTAdapter()
        elif provider in ["hosted_whisper", "openai_whisper"]:
            _stt_adapter = HostedWhisperSTTAdapter()
        else:
            _stt_adapter = MockSTTAdapter()
    return _stt_adapter


def reset_adapters() -> None:
    """Resets adapter singletons (useful for test isolation and runtime reconfiguration)."""
    global _stt_adapter, _translation_adapter, _tts_adapter
    _stt_adapter = None
    _translation_adapter = None
    _tts_adapter = None


def get_translation_adapter() -> BaseTranslationAdapter:
    """
    Returns the configured Translation adapter based on VOICE_TRANSLATION_PROVIDER:
    - 'hosted_translation': HostedTranslationAdapter
    - 'local_indictrans': IndicTrans2TranslationAdapter
    - 'mock_development' (or fallback): MockTranslationAdapter
    """
    global _translation_adapter
    if _translation_adapter is None:
        provider = (settings.VOICE_TRANSLATION_PROVIDER or "mock_development").lower().strip()
        if provider in ["hosted_translation", "openai_translation"]:
            _translation_adapter = HostedTranslationAdapter()
        elif provider in ["local_indictrans", "indictrans2"]:
            _translation_adapter = IndicTrans2TranslationAdapter()
        else:
            _translation_adapter = MockTranslationAdapter()
    return _translation_adapter


def get_tts_adapter() -> BaseTTSAdapter:
    """
    Returns the configured TTS adapter based on VOICE_TTS_PROVIDER:
    - 'hosted_tts' / 'openai_tts': HostedOpenAITTSAdapter
    - 'local_tts' / 'offline_tts': LocalTTSAdapter
    - 'mock_development' (or fallback): MockTTSAdapter
    """
    global _tts_adapter
    if _tts_adapter is None:
        provider = (settings.VOICE_TTS_PROVIDER or "mock_development").lower().strip()
        if provider in ["hosted_tts", "openai_tts"]:
            _tts_adapter = HostedOpenAITTSAdapter()
        elif provider in ["local_tts", "offline_tts"]:
            _tts_adapter = LocalTTSAdapter()
        else:
            _tts_adapter = MockTTSAdapter()
    return _tts_adapter


__all__ = [
    "BaseSTTAdapter",
    "BaseTranslationAdapter",
    "BaseTTSAdapter",
    "STTResult",
    "TranslationResult",
    "TTSResult",
    "MockSTTAdapter",
    "MockTranslationAdapter",
    "MockTTSAdapter",
    "FasterWhisperSTTAdapter",
    "HostedWhisperSTTAdapter",
    "HostedTranslationAdapter",
    "IndicTrans2TranslationAdapter",
    "HostedOpenAITTSAdapter",
    "LocalTTSAdapter",
    "detect_script_language",
    "get_stt_adapter",
    "get_translation_adapter",
    "get_tts_adapter",
    "reset_adapters",
]
