from datetime import datetime, timezone
from typing import Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

MOCK_STT_DISCLAIMER = (
    "MOCK TRANSCRIPTION: Simulated placeholder. No actual speech recognition or audio ML "
    "was performed on the input payload."
)

REAL_STT_DISCLAIMER = (
    "REAL STT: Speech recognized using automated acoustic AI models. Non-emergency assistive "
    "interaction only. Automated transcripts must not be relied upon for clinical diagnosis or "
    "life-critical emergency dispatch."
)

# Supported audio MIME types for speech transcription
SUPPORTED_AUDIO_MIME_TYPES = [
    "audio/wav",
    "audio/x-wav",
    "audio/mpeg",
    "audio/mp3",
    "audio/ogg",
    "audio/webm",
    "audio/x-m4a",
    "audio/flac",
]

MOCK_TRANSLATION_DISCLAIMER = (
    "MOCK TRANSLATION: Simulated placeholder for interface testing. Does not represent a "
    "clinically or linguistically verified translation."
)

REAL_TRANSLATION_DISCLAIMER = (
    "REAL TRANSLATION: Translated using automated multilingual neural machine translation models. "
    "Non-emergency assistive interaction only. Automated translations must not be treated as "
    "verified medical instructions or clinical advice."
)

MOCK_TTS_DISCLAIMER = (
    "MOCK TTS: Simulated audio payload placeholder. No playable acoustic speech was generated."
)

REAL_TTS_DISCLAIMER = (
    "REAL TTS: Acoustic speech synthesized using automated text-to-speech models. "
    "Non-emergency assistive interaction only. Automated speech must not be treated as "
    "clinical instructions or medical diagnoses."
)

# Supported audio formats for text-to-speech synthesis
SUPPORTED_TTS_AUDIO_FORMATS = [
    "audio/mp3",
    "audio/mpeg",
    "audio/wav",
    "audio/x-wav",
    "audio/ogg",
    "audio/aac",
    "audio/opus",
]

VOICE_PRIVACY_NOTICE = (
    "PulseGuardian AI handles voice interactions in ephemeral memory. Explicit patient consent is "
    "mandatory before processing audio data. Raw audio files are not persisted to persistent storage "
    "without affirmative authorization."
)

# Supported language codes: Kannada, English, Hindi, Malayalam, Tamil, Telugu, Urdu
SUPPORTED_LANGUAGE_CODES = ["kn", "en", "hi", "ml", "ta", "te", "ur"]

SUPPORTED_LANGUAGES_REGISTRY = [
    {
        "code": "kn",
        "name": "Kannada",
        "native_name": "ಕನ್ನಡ",
        "script": "Kannada",
        "direction": "ltr",
        "stt_supported": True,
        "translation_supported": True,
        "tts_supported": True,
        "privacy_consent_required": True,
    },
    {
        "code": "en",
        "name": "English",
        "native_name": "English",
        "script": "Latin",
        "direction": "ltr",
        "stt_supported": True,
        "translation_supported": True,
        "tts_supported": True,
        "privacy_consent_required": True,
    },
    {
        "code": "hi",
        "name": "Hindi",
        "native_name": "हिन्दी",
        "script": "Devanagari",
        "direction": "ltr",
        "stt_supported": True,
        "translation_supported": True,
        "tts_supported": True,
        "privacy_consent_required": True,
    },
    {
        "code": "ml",
        "name": "Malayalam",
        "native_name": "മലയാളം",
        "script": "Malayalam",
        "direction": "ltr",
        "stt_supported": True,
        "translation_supported": True,
        "tts_supported": True,
        "privacy_consent_required": True,
    },
    {
        "code": "ta",
        "name": "Tamil",
        "native_name": "தமிழ்",
        "script": "Tamil",
        "direction": "ltr",
        "stt_supported": True,
        "translation_supported": True,
        "tts_supported": True,
        "privacy_consent_required": True,
    },
    {
        "code": "te",
        "name": "Telugu",
        "native_name": "తెలుగు",
        "script": "Telugu",
        "direction": "ltr",
        "stt_supported": True,
        "translation_supported": True,
        "tts_supported": True,
        "privacy_consent_required": True,
    },
    {
        "code": "ur",
        "name": "Urdu",
        "native_name": "اردو",
        "script": "Perso-Arabic",
        "direction": "rtl",
        "stt_supported": True,
        "translation_supported": True,
        "tts_supported": True,
        "privacy_consent_required": True,
    },
]


class LanguageInfo(BaseModel):
    code: str = Field(..., description="ISO-639-1 language code")
    name: str = Field(..., description="English language name")
    native_name: str = Field(..., description="Native script name")
    script: str = Field(..., description="Script identifier")
    direction: str = Field("ltr", description="'ltr' or 'rtl'")
    stt_supported: bool = True
    translation_supported: bool = True
    tts_supported: bool = True
    privacy_consent_required: bool = True


class SupportedLanguagesResponse(BaseModel):
    languages: List[LanguageInfo]
    total_supported: int
    default_language: str
    mock_mode_active: bool
    privacy_notice: str


class SpeechToTextRequest(BaseModel):
    audio_base64: Optional[str] = Field(None, description="Base64-encoded audio payload")
    audio_format: str = Field("audio/wav", description="Audio MIME type ('audio/wav', 'audio/mpeg', etc.)")
    language_hint: Optional[str] = Field("en", description="Optional expected language code ('kn', 'en', 'hi', 'ml', 'ta', 'te', 'ur')")
    consent_confirmed: bool = Field(False, description="Affirmative patient consent for processing voice data")


class SpeechToTextResponse(BaseModel):
    transcript: str
    detected_language: str
    confidence: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Calibrated confidence score if provided by adapter, else None"
    )
    provider: str
    is_mock: bool
    disclaimer: str
    uncertain_speech: bool = Field(
        False,
        description="Flag indicating whether transcription or language detection is uncertain"
    )


class TranslationRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000, description="Source text to translate")
    source_language: Optional[str] = Field(None, description="Source language ISO code (auto-detected if None)")
    target_language: str = Field(..., description="Target language ISO code ('kn', 'en', 'hi', 'ml', 'ta', 'te', 'ur')")
    consent_confirmed: bool = Field(True, description="Affirmative consent for data transmission")


class TranslationResponse(BaseModel):
    original_text: str
    translated_text: str
    source_language: str
    target_language: str
    confidence: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Calibrated confidence score if provided by adapter, else None"
    )
    provider: str
    is_mock: bool
    disclaimer: str
    uncertain_translation: bool = Field(
        False,
        description="Flag indicating whether translation or source language detection is uncertain"
    )


class TextToSpeechRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000, description="Text to synthesize")
    language_code: str = Field(..., description="Language code ('kn', 'en', 'hi', 'ml', 'ta', 'te', 'ur')")
    voice_gender: str = Field("neutral", description="'neutral', 'female', 'male'")
    audio_format: str = Field("audio/mp3", description="Audio container format ('audio/mp3', 'audio/wav', 'audio/ogg')")
    consent_confirmed: bool = Field(True, description="Consent for speech synthesis generation")


class TextToSpeechResponse(BaseModel):
    language_code: str
    audio_payload: str = Field(..., description="Base64-encoded or mock audio payload")
    audio_format: str = Field(..., description="Audio format")
    is_mock: bool = Field(..., description="True if generated by mock placeholder, False for real provider")
    is_playable: bool = Field(..., description="True if payload contains playable acoustic audio")
    provider: str
    disclaimer: str


class VoiceConsentUpdateRequest(BaseModel):
    consent_granted: bool = Field(..., description="True to authorize voice interactions, False to withdraw")
    audio_retention_permitted: bool = Field(False, description="Whether server-side audio retention is permitted (default False)")


class VoiceConsentStatusResponse(BaseModel):
    user_id: int
    consent_granted: bool
    audio_retention_permitted: bool
    privacy_policy_accepted: bool
    updated_at: datetime


# -----------------------------------------------------------------------------
# Multilingual Patient-Caregiver Messaging & Workflow Schemas
# -----------------------------------------------------------------------------

class SendMessageRequest(BaseModel):
    recipient_id: int = Field(..., description="Target User ID of authorized patient or caregiver")
    text: str = Field(..., min_length=1, max_length=5000, description="Message text in sender's language")
    source_language: Optional[str] = Field(None, description="Sender's language code ('kn', 'en', 'hi', 'ml', 'ta', 'te', 'ur')")
    target_language: Optional[str] = Field(None, description="Requested recipient language code")
    auto_translate: bool = Field(True, description="Whether to automatically translate message if languages differ")
    consent_confirmed: bool = Field(True, description="Consent for AI translation processing")
    reply_to_id: Optional[int] = Field(None, description="Optional parent message ID if replying to an earlier message")


class ReplyMessageRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000, description="Reply text in sender's language")
    source_language: Optional[str] = Field(None, description="Sender's language code ('kn', 'en', 'hi', 'ml', 'ta', 'te', 'ur')")
    target_language: Optional[str] = Field(None, description="Requested recipient language code")
    auto_translate: bool = Field(True, description="Whether to translate message automatically if languages differ")
    consent_confirmed: bool = Field(True, description="Affirmative consent for data transmission")


class TranslateMessageRequest(BaseModel):
    target_language: Optional[str] = Field(None, description="Target language code ('kn', 'en', 'hi', 'ml', 'ta', 'te', 'ur'); defaults to user's preferred language")
    consent_confirmed: bool = Field(True, description="Affirmative consent for translation")


class SynthesizeMessageRequest(BaseModel):
    language_code: Optional[str] = Field(None, description="Language to synthesize ('kn', 'en', 'hi', 'ml', 'ta', 'te', 'ur'); defaults to translated or source language")
    voice_gender: str = Field("neutral", description="'neutral', 'female', 'male', or direct voice name")
    audio_format: str = Field("audio/mp3", description="Audio format container ('audio/mp3', 'audio/wav', 'audio/ogg')")
    consent_confirmed: bool = Field(True, description="Affirmative consent for speech synthesis")


class VoiceMessageResponse(BaseModel):
    id: int
    sender_id: int
    recipient_id: int
    source_language: str
    target_language: str
    original_text: str
    translated_text: Optional[str] = None
    is_read: bool
    read_at: Optional[datetime] = None
    delivery_status: str
    translation_status: str
    is_uncertain: bool
    reply_to_id: Optional[int] = None
    audio_payload: Optional[str] = None
    audio_format: Optional[str] = None
    consent_confirmed: bool
    stt_provider: str
    translation_provider: str
    tts_provider: str
    created_at: datetime
    disclaimer: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ConversationPartnerSummary(BaseModel):
    partner_id: int
    full_name: str
    role: str
    preferred_language: str
    relationship_type: Optional[str] = None
    unread_count: int = 0
    last_message_at: Optional[datetime] = None
    last_message_snippet: Optional[str] = None


class ConversationHistoryResponse(BaseModel):
    partner: ConversationPartnerSummary
    total_messages: int
    messages: List[VoiceMessageResponse]


class UnreadCountResponse(BaseModel):
    total_unread: int
    by_sender: Dict[int, int]


class VoiceWorkflowRequest(BaseModel):
    recipient_id: int = Field(..., description="Target User ID of authorized patient or caregiver")
    audio_base64: Optional[str] = Field(None, description="Base64-encoded audio for speech input")
    audio_format: Optional[str] = Field("audio/wav", description="Audio MIME type ('audio/wav', 'audio/mp3', 'audio/ogg', etc.)")
    language_hint: Optional[str] = Field(None, description="Optional STT language hint ('kn', 'en', 'hi', 'ml', 'ta', 'te', 'ur')")
    text: Optional[str] = Field(None, max_length=5000, description="Direct text input (if not providing speech audio)")
    source_language: Optional[str] = Field(None, description="Source language if text provided")
    target_language: Optional[str] = Field(None, description="Target language for translation")
    generate_tts: bool = Field(False, description="Whether to synthesize acoustic speech audio")
    voice_gender: str = Field("neutral", description="'neutral', 'female', 'male', or direct voice name")
    tts_audio_format: str = Field("audio/mp3", description="Audio container for TTS output")
    consent_confirmed: bool = Field(True, description="Affirmative patient/caregiver consent")
    reply_to_id: Optional[int] = Field(None, description="Parent message ID if replying")


class VoiceWorkflowResponse(BaseModel):
    message_id: int
    sender_id: int
    recipient_id: int
    stage_statuses: Dict[str, str] = Field(..., description="Statuses of workflow stages (audio_validation, stt_transcription, language_detection, translation, tts_synthesis)")
    source_language: str
    target_language: str
    original_text: str
    translated_text: Optional[str] = None
    uncertain_speech: bool = False
    uncertain_translation: bool = False
    is_uncertain: bool = False
    audio_payload: Optional[str] = None
    audio_format: Optional[str] = None
    stt_provider: str
    translation_provider: str
    tts_provider: str
    disclaimers: List[str]
    created_at: datetime

