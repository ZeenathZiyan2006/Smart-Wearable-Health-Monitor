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

        # Clean conversational and healthcare translation dictionary
        clean_input = text.strip().lower()

        # Check if text corresponds to a known draft phrase key
        for key, lang_map in DRAFT_EMERGENCY_DICTIONARY.items():
            for l_code, phrase in lang_map.items():
                if text.strip() == phrase.strip():
                    translated_val = get_draft_emergency_phrase(key, tgt)
                    return TranslationResult(
                        original_text=text,
                        translated_text=translated_val,
                        source_language=src,
                        target_language=tgt,
                        confidence=0.98,
                        provider=MOCK_PROVIDER_NAME,
                        is_mock=False,
                        disclaimer=MOCK_TRANSLATION_DISCLAIMER,
                        uncertain_translation=False
                    )

        SMART_DICT = {
            'namaskara': {'en': 'Hello / Greetings! Wishing you good health.', 'kn': 'ನಮಸ್ಕಾರ', 'hi': 'नमस्ते', 'ta': 'வணக்கம்', 'te': 'నమస్కారం', 'ml': 'നമസ്കാരം'},
            'namaskra': {'en': 'Hello / Greetings! Wishing you good health.', 'kn': 'ನಮಸ್ಕಾರ', 'hi': 'नमस्ते', 'ta': 'வணக்கம்', 'te': 'నమస్కారం', 'ml': 'നമസ്കാരം'},
            'ನಮಸ್ಕಾರ': {'en': 'Hello / Greetings! Wishing you good health.', 'kn': 'ನಮಸ್ಕಾರ', 'hi': 'नमस्ते', 'ta': 'வணக்கம்', 'te': 'నమస్కారం', 'ml': 'നമസ്കാരം'},
            'oota aayitha': {'en': 'Did you have your meals / lunch?', 'kn': 'ಊಟ ಆಯ್ತಾ?', 'hi': 'क्या आपने खाना खा लिया?', 'ta': 'சாப்பிட்டீர்களா?', 'te': 'భోజనం చేశారా?', 'ml': 'ഭക്ഷണം കഴിച്ചോ?'},
            'oota': {'en': 'Did you have your meals / lunch?', 'kn': 'ಊಟ ಆಯ್ತಾ?', 'hi': 'क्या आपने खाना खा लिया?', 'ta': 'சாப்பிட்டீர்களா?', 'te': 'భోజనం చేశారా?', 'ml': 'ഭക്ഷണം കഴിച്ചോ?'},
            'ಊಟ ಆಯ್ತಾ': {'en': 'Did you have your meals / lunch?', 'kn': 'ಊಟ ಆಯ್ತಾ?', 'hi': 'क्या आपने खाना खा लिया?', 'ta': 'சாப்பிட்டீர்களா?', 'te': 'భోజనం చేశారా?', 'ml': 'ഭക്ഷണം കഴിച്ചോ?'},
            'neeru kudide': {'en': 'I drank water and hydrated myself.', 'kn': 'ನೀರು ಕುಡಿದೆ.', 'hi': 'मैंने पानी पी लिया।', 'ta': 'நான் தண்ணீர் குடித்தேன்.', 'te': 'నేను నీరు త్రాగాను.', 'ml': 'ഞാൻ വെള്ളം കുടിച്ചു.'},
            'neeru': {'en': 'I need water / drinking water.', 'kn': 'ನೀರು', 'hi': 'पानी', 'ta': 'தண்ணீர்', 'te': 'నీరు', 'ml': 'വെള്ളം'},
            'mathre thegedukonde': {'en': 'I took the prescribed medicine / vitamins.', 'kn': 'ಮಾತ್ರೆಗಳನ್ನು ತೆಗೆದುಕೊಂಡೆ.', 'hi': 'मैंने दवाइयां ले ली हैं।', 'ta': 'நான் மாத்திரைகளை எடுத்துக்கொண்டேன்.', 'te': 'నేను మందులు వేసుకున్నాను.', 'ml': 'ഞാൻ ഗുളികകൾ കഴിച്ചു.'},
            'ಮಾತ್ರೆಗಳನ್ನು ತೆಗೆದುಕೊಂಡೆ': {'en': 'I took the prescribed medicine / vitamins.', 'kn': 'ಮಾತ್ರೆಗಳನ್ನು ತೆಗೆದುಕೊಂಡೆ.', 'hi': 'मैंने दवाइयां ले ली हैं।', 'ta': 'நான் மாத்திரைகளை எடுத்துக்கொண்டேன்.', 'te': 'నేను మందులు వేసుకున్నాను.', 'ml': 'ഞാൻ ഗുളികകൾ കഴിച്ചു.'},
            'nanage novagide': {'en': 'I am experiencing physical pain / discomfort.', 'kn': 'ನನಗೆ ನೋವಾಗುತ್ತಿದೆ.', 'hi': 'मुझे दर्द महसूस हो रहा है।', 'ta': 'எனக்கு உடலில் வலி உள்ளது.', 'te': 'నాకు నొప్పిగా ఉంది.', 'ml': 'എനിക്ക് വേദന അനുഭവപ്പെടുന്നു.'},
            'nanage novaaguttide': {'en': 'I am experiencing physical pain / discomfort.', 'kn': 'ನನಗೆ ನೋವಾಗುತ್ತಿದೆ.', 'hi': 'मुझे दर्द महसूस हो रहा है।', 'ta': 'எனக்கு உடலில் வலி உள்ளது.', 'te': 'నాకు నొప్పిగా ఉంది.', 'ml': 'എനിക്ക് വേദന അനുഭവപ്പെടുന്നു.'},
            'ನನಗೆ ನೋವಾಗುತ್ತಿದೆ': {'en': 'I am experiencing physical pain / discomfort.', 'kn': 'ನನಗೆ ನೋವಾಗುತ್ತಿದೆ.', 'hi': 'मुझे दर्द महसूस हो रहा है।', 'ta': 'எனக்கு உடலில் வலி உள்ளது.', 'te': 'నాకు నొప్పిగా ఉంది.', 'ml': 'എനിക്ക് വേദന അനുഭവപ്പെടുന്നു.'},
            'hegiddeera': {'en': 'How are you feeling today?', 'kn': 'ಹೇಗಿದ್ದೀರಾ?', 'hi': 'आप आज कैसे हैं?', 'ta': 'நீங்கள் எப்படி இருக்கிறீர்கள்?', 'te': 'మీరు ఎలా ఉన్నారు?', 'ml': 'സുഖമാണോ?'},
            'ಹೇಗಿದ್ದೀರಾ': {'en': 'How are you feeling today?', 'kn': 'ಹೇಗಿದ್ದೀರಾ?', 'hi': 'आप आज कैसे हैं?', 'ta': 'நீங்கள் எப்படி இருக்கிறீர்கள்?', 'te': 'మీరు ఎలా ఉన్నారు?', 'ml': 'സുഖമാണോ?'},
            'help': {'en': 'I need immediate medical assistance / help.', 'kn': 'ನನಗೆ ತುರ್ತು ವೈದ್ಯಕೀಯ ಸಹಾಯ ಬೇಕು.', 'hi': 'मुझे तत्काल चिकित्सा सहायता चाहिए।', 'ta': 'எனக்கு உடனடி உதவி தேவை.', 'te': 'నాకు అత్యవసర సహాయం కావాలి.', 'ml': 'എനിക്ക് അടിയന്തര സഹായം വേണം.'},
            'sahaya': {'en': 'I need immediate medical assistance / help.', 'kn': 'ನನಗೆ ತುರ್ತು ವೈದ್ಯಕೀಯ ಸಹಾಯ ಬೇಕು.', 'hi': 'मुझे तत्काल चिकित्सा सहायता चाहिए।', 'ta': 'எனக்கு உடனடி உதவி தேவை.', 'te': 'నాకు అత్యవసర సహాయం కావాలి.', 'ml': 'എനിക്ക് അടിയന്തര സഹായം വേണം.'},
            'good morning': {'en': 'Good morning! Did you remember to drink water and take your morning vitamins?', 'kn': 'ಶುಭೋದಯ! ನೀವು ನೀರು ಕುಡಿದು ಬೆಳಗಿನ ಜೀವಸತ್ವಗಳನ್ನು ತೆಗೆದುಕೊಳ್ಳಲು ನೆನಪಿಸಿಕೊಂಡಿದ್ದೀರಾ?', 'hi': 'शुभ प्रभात! क्या आपने पानी पिया और सुबह की दवाइयां लीं?', 'ta': 'காலை வணக்கம்! தண்ணீர் குடித்து காலை மருந்துகளை எடுத்துக்கொண்டீர்களா?', 'te': 'శుభోదయం! నీరు తాగి ఉదయపు మందులు తీసుకున్నారా?', 'ml': 'സുപ്രഭാതം! വെള്ളം കുടിച്ച് രാവിലത്തെ മരുന്നുകൾ കഴിച്ചോ?'},
            'yes sarah': {'en': 'Yes Sarah, I took the vitamins after breakfast.', 'kn': 'ಹೌದು ಸಾರಾ, ನಾನು ಉಪಾಹಾರದ ನಂತರ ಮಾತ್ರೆಗಳನ್ನು ತೆಗೆದುಕೊಂಡೆ.', 'hi': 'हाँ सारा, मैंने नाश्ते के बाद विटामिन ले लिए।', 'ta': 'ஆம் சாரா, நான் காலை உணவுக்குப் பிறகு வைட்டமின்களை எடுத்துக்கொண்டேன்.', 'te': 'అవును సారా, నేను అల్పాహారం తర్వాత విటమిన్లు తీసుకున్నాను.', 'ml': 'അതെ സാറാ, പ്രഭാതഭക്ഷണത്തിന് ശേഷം ഞാൻ വിറ്റാമിനുകൾ കഴിച്ചു.'},
        }

        # Check direct or substring match
        matched_trans = None
        for k, v in SMART_DICT.items():
            if k in clean_input or clean_input in k:
                matched_trans = v.get(tgt) or v.get('en') or text
                break

        if not matched_trans:
            matched_trans = f"[Simulated {tgt.upper()} Translation]: {text}"

        return TranslationResult(
            original_text=text,
            translated_text=matched_trans,
            source_language=src,
            target_language=tgt,
            confidence=0.95,
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
