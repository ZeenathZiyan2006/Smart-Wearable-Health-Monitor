import base64
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.core.config import settings
from app.core.security import decode_token
from app.models.user import User
from app.models.voice import VoiceAuditLog, VoiceConsent, VoiceMessageLog
from app.schemas.voice import (
    LanguageInfo,
    SpeechToTextRequest,
    SpeechToTextResponse,
    SupportedLanguagesResponse,
    TextToSpeechRequest,
    TextToSpeechResponse,
    TranslationRequest,
    TranslationResponse,
    VoiceConsentStatusResponse,
    VoiceConsentUpdateRequest,
    SendMessageRequest,
    ReplyMessageRequest,
    TranslateMessageRequest,
    SynthesizeMessageRequest,
    VoiceMessageResponse,
    ConversationPartnerSummary,
    ConversationHistoryResponse,
    UnreadCountResponse,
    VoiceWorkflowRequest,
    VoiceWorkflowResponse,
    SUPPORTED_AUDIO_MIME_TYPES,
    SUPPORTED_LANGUAGE_CODES,
    SUPPORTED_LANGUAGES_REGISTRY,
    SUPPORTED_TTS_AUDIO_FORMATS,
    VOICE_PRIVACY_NOTICE,
    MOCK_TRANSLATION_DISCLAIMER,
    REAL_TRANSLATION_DISCLAIMER,
)
from app.services.voice.adapters import (
    get_stt_adapter,
    get_translation_adapter,
    get_tts_adapter,
)
from app.services.voice.audio_validator import inspect_audio_duration
from app.services.voice.messaging_service import (
    connection_manager,
    execute_voice_workflow,
    get_conversation_messages,
    get_conversations_summary,
    get_message_by_id,
    mark_all_messages_read_in_conversation,
    mark_message_as_read,
    send_multilingual_message,
    synthesize_message_speech_on_demand,
    translate_message_on_demand,
    validate_patient_caregiver_relationship,
)

router = APIRouter()


def _check_voice_consent(db: Session, user_id: int, request_consent_confirmed: bool) -> bool:
    """
    Validates affirmative user consent for voice and audio processing.
    Checks either explicit request-level consent flag or persistent user consent preference.
    """
    if not settings.VOICE_ENABLE_CONSENT_ENFORCEMENT:
        return True

    if request_consent_confirmed:
        return True

    consent_record = db.query(VoiceConsent).filter(VoiceConsent.user_id == user_id).first()
    if consent_record and consent_record.consent_granted:
        return True

    return False


# -----------------------------------------------------------------------------
# 1. Supported Languages Metadata
# -----------------------------------------------------------------------------
@router.get("/languages", response_model=SupportedLanguagesResponse, status_code=status.HTTP_200_OK)
def get_supported_languages(
    current_user: User = Depends(get_current_active_user)
) -> SupportedLanguagesResponse:
    """
    Returns detailed language support metadata for Kannada, English, Hindi,
    Malayalam, Tamil, Telugu, and Urdu along with active provider readiness
    and privacy consent notices.
    """
    languages = [LanguageInfo(**lang) for lang in SUPPORTED_LANGUAGES_REGISTRY]
    return SupportedLanguagesResponse(
        languages=languages,
        total_supported=len(languages),
        default_language=settings.DEFAULT_SYSTEM_LANGUAGE,
        mock_mode_active=(settings.VOICE_STT_PROVIDER == "mock_development"),
        privacy_notice=VOICE_PRIVACY_NOTICE
    )


# -----------------------------------------------------------------------------
# 2. Voice Processing Consent Management
# -----------------------------------------------------------------------------
@router.get("/consent", response_model=VoiceConsentStatusResponse, status_code=status.HTTP_200_OK)
def get_user_voice_consent(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> VoiceConsentStatusResponse:
    """Retrieves current voice processing consent and audio retention preferences for the user."""
    consent_record = db.query(VoiceConsent).filter(VoiceConsent.user_id == current_user.id).first()
    now = datetime.now(timezone.utc)
    if not consent_record:
        return VoiceConsentStatusResponse(
            user_id=current_user.id,
            consent_granted=False,
            audio_retention_permitted=False,
            privacy_policy_accepted=True,
            updated_at=now
        )

    return VoiceConsentStatusResponse(
        user_id=consent_record.user_id,
        consent_granted=consent_record.consent_granted,
        audio_retention_permitted=consent_record.audio_retention_permitted,
        privacy_policy_accepted=consent_record.privacy_policy_accepted,
        updated_at=consent_record.updated_at
    )


@router.post("/consent", response_model=VoiceConsentStatusResponse, status_code=status.HTTP_200_OK)
def update_user_voice_consent(
    payload: VoiceConsentUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> VoiceConsentStatusResponse:
    """Updates affirmative voice data processing consent and retention preferences."""
    now = datetime.now(timezone.utc)
    consent_record = db.query(VoiceConsent).filter(VoiceConsent.user_id == current_user.id).first()

    if not consent_record:
        consent_record = VoiceConsent(
            user_id=current_user.id,
            consent_granted=payload.consent_granted,
            audio_retention_permitted=payload.audio_retention_permitted,
            privacy_policy_accepted=True,
            created_at=now,
            updated_at=now
        )
        db.add(consent_record)
    else:
        consent_record.consent_granted = payload.consent_granted
        consent_record.audio_retention_permitted = payload.audio_retention_permitted
        consent_record.updated_at = now

    # Log audit event
    audit = VoiceAuditLog(
        user_id=current_user.id,
        operation_type="consent_update",
        detected_language=None,
        input_character_count=0,
        output_character_count=0,
        is_mock=True,
        provider="system_auth",
        created_at=now
    )
    db.add(audit)
    db.commit()
    db.refresh(consent_record)

    return VoiceConsentStatusResponse(
        user_id=consent_record.user_id,
        consent_granted=consent_record.consent_granted,
        audio_retention_permitted=consent_record.audio_retention_permitted,
        privacy_policy_accepted=consent_record.privacy_policy_accepted,
        updated_at=consent_record.updated_at
    )


# -----------------------------------------------------------------------------
# 3. Speech-to-Text Transcription (Real / Mock STT Adapters)
# -----------------------------------------------------------------------------
@router.post("/transcribe", response_model=SpeechToTextResponse, status_code=status.HTTP_200_OK)
def transcribe_audio_payload(
    payload: SpeechToTextRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> SpeechToTextResponse:
    """
    Transcribes audio payload using the configured STT provider (local_whisper, hosted_whisper, or mock).
    Enforces privacy consent, supported MIME types, max 10MB payload size, and language validation.
    Returns uncalibrated confidence safely as None and flags uncertain/unsupported speech.
    """
    if not _check_voice_consent(db, current_user.id, payload.consent_confirmed):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Consent required: Affirmative user authorization is mandatory before processing voice data."
        )

    # 1. Validate audio format / MIME type
    audio_format = (payload.audio_format or "").lower().strip()
    if audio_format not in SUPPORTED_AUDIO_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported audio MIME type '{payload.audio_format}'. Supported formats: {', '.join(SUPPORTED_AUDIO_MIME_TYPES)}"
        )

    # 2. Validate language hint if provided
    if payload.language_hint:
        hint_lang = payload.language_hint.lower().strip()
        if hint_lang not in SUPPORTED_LANGUAGE_CODES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported language code '{payload.language_hint}'. Supported: {', '.join(SUPPORTED_LANGUAGE_CODES)}"
            )
    else:
        hint_lang = None

    # 3. Validate audio payload presence
    if not payload.audio_base64 or not payload.audio_base64.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Audio payload is required and cannot be empty."
        )

    # 4. Validate base64 encoding
    try:
        audio_bytes = base64.b64decode(payload.audio_base64.strip(), validate=True)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid base64 encoding in audio payload."
        )

    if len(audio_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Decoded audio payload is empty."
        )

    # 5. Validate audio payload size (10 MB maximum limit)
    if len(audio_bytes) > settings.VOICE_MAX_AUDIO_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Audio payload size ({len(audio_bytes)} bytes) exceeds the maximum allowed limit of {settings.VOICE_MAX_AUDIO_SIZE_BYTES} bytes (10 MB)."
        )

    # 6. Validate audio duration pre-flight (in-memory)
    try:
        duration_seconds = inspect_audio_duration(audio_bytes, audio_format)
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Audio validation failed: {str(val_err)}"
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Audio validation failed: Could not parse audio duration."
        )

    if duration_seconds > settings.VOICE_MAX_AUDIO_DURATION_SECONDS:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=(
                f"Audio duration ({duration_seconds:.2f}s) exceeds the maximum allowed limit "
                f"of {settings.VOICE_MAX_AUDIO_DURATION_SECONDS} seconds."
            )
        )

    # 7. Execute STT transcription
    stt_adapter = get_stt_adapter()
    try:
        result = stt_adapter.transcribe(
            audio_bytes=audio_bytes,
            content_type=audio_format,
            hint_language=hint_lang
        )
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Audio processing validation error: {str(val_err)}"
        )
    except TimeoutError as timeout_err:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=f"STT provider timed out: {str(timeout_err)}"
        )
    except RuntimeError as rt_err:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"STT service unavailable: {str(rt_err)}"
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred during speech-to-text processing."
        )

    # 7. Ephemeral audit logging (never logs raw audio bytes)
    audit = VoiceAuditLog(
        user_id=current_user.id,
        operation_type="stt",
        detected_language=result.detected_language,
        input_character_count=len(audio_bytes),
        output_character_count=len(result.transcript),
        is_mock=result.is_mock,
        provider=result.provider,
        created_at=datetime.now(timezone.utc)
    )
    db.add(audit)
    db.commit()

    return SpeechToTextResponse(
        transcript=result.transcript,
        detected_language=result.detected_language,
        confidence=result.confidence,
        provider=result.provider,
        is_mock=result.is_mock,
        disclaimer=result.disclaimer,
        uncertain_speech=result.uncertain_speech
    )


# -----------------------------------------------------------------------------
# 4. Multilingual Text Translation (Real & Mock Translation Adapters)
# -----------------------------------------------------------------------------
@router.post("/translate", response_model=TranslationResponse, status_code=status.HTTP_200_OK)
def translate_text(
    payload: TranslationRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> TranslationResponse:
    """
    Translates text between the 7 supported languages (kn, en, hi, ml, ta, te, ur)
    using the configured translation provider (hosted_translation, local_indictrans, or mock).
    Enforces privacy consent, input text length constraints, directional pair validation,
    and returns uncalibrated confidence safely as None with uncertainty tracking.
    """
    if not _check_voice_consent(db, current_user.id, payload.consent_confirmed):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Consent required: Affirmative user authorization is mandatory before translating text."
        )

    # 1. Validate text presence and length
    if not payload.text or not payload.text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Translation source text cannot be empty or whitespace only."
        )

    if len(payload.text) > settings.VOICE_MAX_TRANSLATION_CHARS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Translation text length ({len(payload.text)} chars) exceeds maximum limit of {settings.VOICE_MAX_TRANSLATION_CHARS} characters."
        )

    # 2. Validate target language
    tgt_lang = (payload.target_language or "").lower().strip()
    if tgt_lang not in SUPPORTED_LANGUAGE_CODES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported target language '{payload.target_language}'. Supported: {', '.join(SUPPORTED_LANGUAGE_CODES)}"
        )

    # 3. Validate source language if explicitly supplied
    src_lang = payload.source_language.lower().strip() if payload.source_language else None
    if src_lang and src_lang not in SUPPORTED_LANGUAGE_CODES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported source language '{payload.source_language}'. Supported: {', '.join(SUPPORTED_LANGUAGE_CODES)}"
        )

    # 4. Execute translation with structured error mapping
    translator = get_translation_adapter()
    try:
        result = translator.translate(
            text=payload.text.strip(),
            source_language=src_lang,
            target_language=tgt_lang
        )
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Translation input validation error: {str(val_err)}"
        )
    except TimeoutError as timeout_err:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=f"Translation provider timed out: {str(timeout_err)}"
        )
    except ConnectionError as conn_err:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Translation provider connection error: {str(conn_err)}"
        )
    except RuntimeError as rt_err:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Translation service unavailable: {str(rt_err)}"
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred during text translation."
        )

    # 5. Ephemeral audit logging (metadata only; never stores sensitive text)
    audit = VoiceAuditLog(
        user_id=current_user.id,
        operation_type="translation",
        detected_language=result.source_language,
        input_character_count=len(payload.text),
        output_character_count=len(result.translated_text),
        is_mock=result.is_mock,
        provider=result.provider,
        created_at=datetime.now(timezone.utc)
    )
    db.add(audit)
    db.commit()

    return TranslationResponse(
        original_text=result.original_text,
        translated_text=result.translated_text,
        source_language=result.source_language,
        target_language=result.target_language,
        confidence=result.confidence,
        provider=result.provider,
        is_mock=result.is_mock,
        disclaimer=result.disclaimer,
        uncertain_translation=result.uncertain_translation
    )


# -----------------------------------------------------------------------------
# 5. Text-to-Speech Synthesis (Hosted & Mock Adapters)
# -----------------------------------------------------------------------------
@router.post("/synthesize", response_model=TextToSpeechResponse, status_code=status.HTTP_200_OK)
def synthesize_speech(
    payload: TextToSpeechRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> TextToSpeechResponse:
    """
    Synthesizes text into spoken audio using the configured TTS adapter (Hosted OpenAI or Mock).
    Enforces affirmative consent, text character limits, and safe in-memory base64 response delivery.
    """
    # 1. Affirmative user consent verification
    if not _check_voice_consent(db, current_user.id, payload.consent_confirmed):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Consent required: Affirmative user authorization is mandatory before generating synthesized audio."
        )

    # 2. Validate input text
    cleaned_text = (payload.text or "").strip()
    if not cleaned_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Text to synthesize cannot be empty."
        )

    if len(cleaned_text) > settings.VOICE_MAX_TTS_CHARS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Text length ({len(cleaned_text)} chars) exceeds maximum limit of "
                f"{settings.VOICE_MAX_TTS_CHARS} characters."
            )
        )

    # 3. Validate language code
    lang_code = payload.language_code.lower().strip()
    if lang_code not in SUPPORTED_LANGUAGE_CODES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported language code '{payload.language_code}'. Supported: {', '.join(SUPPORTED_LANGUAGE_CODES)}"
        )

    # 4. Validate audio format
    audio_format = (payload.audio_format or "audio/mp3").lower().strip()
    if audio_format not in SUPPORTED_TTS_AUDIO_FORMATS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Unsupported audio format '{payload.audio_format}'. "
                f"Supported formats: {', '.join(SUPPORTED_TTS_AUDIO_FORMATS)}"
            )
        )

    # 5. Validate voice gender / voice identifier
    voice_gender = (payload.voice_gender or "neutral").lower().strip()
    valid_voices = {"neutral", "female", "male", "alloy", "echo", "fable", "onyx", "nova", "shimmer"}
    if voice_gender not in valid_voices:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid voice identifier '{payload.voice_gender}'. Allowed: {', '.join(sorted(valid_voices))}"
        )

    # 6. Execute speech synthesis with structured error mapping
    tts_adapter = get_tts_adapter()
    try:
        result = tts_adapter.synthesize(
            text=cleaned_text,
            language_code=lang_code,
            voice_gender=voice_gender,
            audio_format=audio_format,
        )
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"TTS input validation error: {str(val_err)}"
        )
    except TimeoutError as timeout_err:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=f"TTS provider timed out: {str(timeout_err)}"
        )
    except ConnectionError as conn_err:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"TTS provider connection error: {str(conn_err)}"
        )
    except RuntimeError as rt_err:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"TTS service unavailable: {str(rt_err)}"
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred during speech synthesis."
        )

    # 7. Ephemeral audit logging (metadata only; never stores sensitive audio or text)
    audit = VoiceAuditLog(
        user_id=current_user.id,
        operation_type="tts",
        detected_language=result.language_code,
        input_character_count=len(payload.text),
        output_character_count=len(result.audio_payload),
        is_mock=result.is_mock,
        provider=result.provider,
        created_at=datetime.now(timezone.utc)
    )
    db.add(audit)
    db.commit()

    return TextToSpeechResponse(
        language_code=result.language_code,
        audio_payload=result.audio_payload,
        audio_format=result.audio_format,
        is_mock=result.is_mock,
        is_playable=result.is_playable,
        provider=result.provider,
        disclaimer=result.disclaimer
    )


# -----------------------------------------------------------------------------
# 6. Patient-Caregiver Multilingual Messaging & Real-Time Communication
# -----------------------------------------------------------------------------

@router.get("/conversations", response_model=List[ConversationPartnerSummary], status_code=status.HTTP_200_OK)
def list_conversations(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> List[ConversationPartnerSummary]:
    """
    Lists conversation summaries for all authorized patient-caregiver partners of the authenticated user.
    Enforces strict relationship verification and includes unread counts and latest message snippets.
    """
    return get_conversations_summary(db, current_user)


@router.get("/conversations/{partner_id}", response_model=ConversationHistoryResponse, status_code=status.HTTP_200_OK)
def get_conversation_history(
    partner_id: int,
    limit: int = Query(50, ge=1, le=100, description="Max messages to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    since: Optional[datetime] = Query(None, description="Filter messages created after this timestamp"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> ConversationHistoryResponse:
    """
    Retrieves chronological message history between the current user and an authorized partner.
    Rejects unauthorized access with HTTP 403.
    """
    if not validate_patient_caregiver_relationship(db, current_user.id, partner_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: You are not authorized to view conversations with this user."
        )

    partner = db.query(User).filter(User.id == partner_id, User.is_active.is_(True)).first()
    if not partner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Partner user with ID {partner_id} not found."
        )

    messages = get_conversation_messages(db, current_user, partner_id, limit=limit, offset=offset, since=since)
    total_count = len(messages)

    # Compute unread count from this partner
    unread_cnt = db.query(VoiceMessageLog).filter(
        VoiceMessageLog.sender_id == partner_id,
        VoiceMessageLog.recipient_id == current_user.id,
        VoiceMessageLog.is_read.is_(False)
    ).count()

    rel_type = partner.caregiver_profile.relationship_type if partner.caregiver_profile else None

    partner_summary = ConversationPartnerSummary(
        partner_id=partner.id,
        full_name=partner.full_name,
        role=partner.role,
        preferred_language=partner.preferred_language or "en",
        relationship_type=rel_type,
        unread_count=unread_cnt,
        last_message_at=messages[-1].created_at if messages else None,
        last_message_snippet=messages[-1].original_text[:60] if messages else None
    )

    formatted_messages = []
    for m in messages:
        disclaimer = REAL_TRANSLATION_DISCLAIMER if m.translation_provider != "mock_development" else MOCK_TRANSLATION_DISCLAIMER
        msg_dict = {
            "id": m.id,
            "sender_id": m.sender_id,
            "recipient_id": m.recipient_id,
            "source_language": m.source_language,
            "target_language": m.target_language,
            "original_text": m.original_text,
            "translated_text": m.translated_text,
            "is_read": m.is_read,
            "read_at": m.read_at,
            "delivery_status": m.delivery_status,
            "translation_status": m.translation_status,
            "is_uncertain": m.is_uncertain,
            "reply_to_id": m.reply_to_id,
            "audio_payload": m.audio_payload,
            "audio_format": m.audio_format,
            "consent_confirmed": m.consent_confirmed,
            "stt_provider": m.stt_provider,
            "translation_provider": m.translation_provider,
            "tts_provider": m.tts_provider,
            "created_at": m.created_at,
            "disclaimer": disclaimer if m.translated_text else None,
        }
        formatted_messages.append(VoiceMessageResponse(**msg_dict))

    return ConversationHistoryResponse(
        partner=partner_summary,
        total_messages=total_count,
        messages=formatted_messages
    )


@router.post("/conversations/{partner_id}/read-all", status_code=status.HTTP_200_OK)
def mark_conversation_as_read(
    partner_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Marks all unread messages received from an authorized partner as read.
    """
    count = mark_all_messages_read_in_conversation(db, partner_id, current_user)
    return {"marked_read_count": count, "partner_id": partner_id}


@router.post("/messages", response_model=VoiceMessageResponse, status_code=status.HTTP_201_CREATED)
def send_message(
    payload: SendMessageRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> VoiceMessageResponse:
    """
    Sends a multilingual text message to an authorized patient or caregiver.
    Automatically translates into recipient's preferred language if different and consent is granted.
    Preserves original text and translated text separately without destructive overwrite.
    """
    msg = send_multilingual_message(
        db=db,
        sender=current_user,
        recipient_id=payload.recipient_id,
        text=payload.text,
        source_language=payload.source_language,
        target_language=payload.target_language,
        auto_translate=payload.auto_translate,
        consent_confirmed=payload.consent_confirmed,
        reply_to_id=payload.reply_to_id,
    )
    disclaimer = REAL_TRANSLATION_DISCLAIMER if msg.translation_provider != "mock_development" else MOCK_TRANSLATION_DISCLAIMER
    resp = VoiceMessageResponse.model_validate(msg)
    resp.disclaimer = disclaimer if msg.translated_text else None
    return resp


@router.get("/messages/unread-count", response_model=UnreadCountResponse, status_code=status.HTTP_200_OK)
def get_unread_messages_count(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> UnreadCountResponse:
    """Returns the total number of unread messages and breakdown by sender."""
    unread_msgs = db.query(VoiceMessageLog).filter(
        VoiceMessageLog.recipient_id == current_user.id,
        VoiceMessageLog.is_read.is_(False)
    ).all()

    by_sender: Dict[int, int] = {}
    for m in unread_msgs:
        by_sender[m.sender_id] = by_sender.get(m.sender_id, 0) + 1

    return UnreadCountResponse(
        total_unread=len(unread_msgs),
        by_sender=by_sender
    )


@router.get("/messages/{message_id}", response_model=VoiceMessageResponse, status_code=status.HTTP_200_OK)
def get_message(
    message_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> VoiceMessageResponse:
    """Retrieves specific message details with strict participant authorization."""
    msg = get_message_by_id(db, message_id, current_user)
    disclaimer = REAL_TRANSLATION_DISCLAIMER if msg.translation_provider != "mock_development" else MOCK_TRANSLATION_DISCLAIMER
    resp = VoiceMessageResponse.model_validate(msg)
    resp.disclaimer = disclaimer if msg.translated_text else None
    return resp


@router.post("/messages/{message_id}/reply", response_model=VoiceMessageResponse, status_code=status.HTTP_201_CREATED)
def reply_to_message(
    message_id: int,
    payload: ReplyMessageRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> VoiceMessageResponse:
    """Replies directly to an existing conversation message."""
    parent_msg = get_message_by_id(db, message_id, current_user)
    recipient_id = parent_msg.sender_id if parent_msg.sender_id != current_user.id else parent_msg.recipient_id

    msg = send_multilingual_message(
        db=db,
        sender=current_user,
        recipient_id=recipient_id,
        text=payload.text,
        source_language=payload.source_language,
        target_language=payload.target_language,
        auto_translate=payload.auto_translate,
        consent_confirmed=payload.consent_confirmed,
        reply_to_id=parent_msg.id,
    )
    disclaimer = REAL_TRANSLATION_DISCLAIMER if msg.translation_provider != "mock_development" else MOCK_TRANSLATION_DISCLAIMER
    resp = VoiceMessageResponse.model_validate(msg)
    resp.disclaimer = disclaimer if msg.translated_text else None
    return resp


@router.post("/messages/{message_id}/translate", response_model=VoiceMessageResponse, status_code=status.HTTP_200_OK)
def translate_message(
    message_id: int,
    payload: TranslateMessageRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> VoiceMessageResponse:
    """Translates an existing message on demand into requested or preferred language."""
    msg = translate_message_on_demand(
        db=db,
        message_id=message_id,
        user=current_user,
        target_language=payload.target_language,
        consent_confirmed=payload.consent_confirmed,
    )
    disclaimer = REAL_TRANSLATION_DISCLAIMER if msg.translation_provider != "mock_development" else MOCK_TRANSLATION_DISCLAIMER
    resp = VoiceMessageResponse.model_validate(msg)
    resp.disclaimer = disclaimer
    return resp


@router.post("/messages/{message_id}/synthesize", response_model=TextToSpeechResponse, status_code=status.HTTP_200_OK)
def synthesize_message_audio(
    message_id: int,
    payload: SynthesizeMessageRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> TextToSpeechResponse:
    """Synthesizes speech audio for an existing message on demand."""
    result = synthesize_message_speech_on_demand(
        db=db,
        message_id=message_id,
        user=current_user,
        language_code=payload.language_code,
        voice_gender=payload.voice_gender,
        audio_format=payload.audio_format,
        consent_confirmed=payload.consent_confirmed,
    )
    return TextToSpeechResponse(
        language_code=result["language_code"],
        audio_payload=result["audio_payload"],
        audio_format=result["audio_format"],
        is_mock=result["is_mock"],
        is_playable=result["is_playable"],
        provider=result["provider"],
        disclaimer=result["disclaimer"],
    )


@router.patch("/messages/{message_id}/read", response_model=VoiceMessageResponse, status_code=status.HTTP_200_OK)
def mark_read(
    message_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> VoiceMessageResponse:
    """Marks a message as read by the intended recipient."""
    msg = mark_message_as_read(db, message_id, current_user)
    disclaimer = REAL_TRANSLATION_DISCLAIMER if msg.translation_provider != "mock_development" else MOCK_TRANSLATION_DISCLAIMER
    resp = VoiceMessageResponse.model_validate(msg)
    resp.disclaimer = disclaimer if msg.translated_text else None
    return resp


# -----------------------------------------------------------------------------
# 7. End-to-End Multilingual Voice Workflow Execution
# -----------------------------------------------------------------------------

@router.post("/workflow/dispatch", response_model=VoiceWorkflowResponse, status_code=status.HTTP_200_OK)
def dispatch_voice_workflow(
    payload: VoiceWorkflowRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> VoiceWorkflowResponse:
    """
    Executes the complete multilingual voice workflow end-to-end:
    Patient speech -> validation -> STT -> language detection -> translation -> persistence -> optional TTS.
    Also handles text-only workflows with explicit stage statuses and comprehensive error handling.
    """
    res = execute_voice_workflow(
        db=db,
        sender=current_user,
        recipient_id=payload.recipient_id,
        audio_base64=payload.audio_base64,
        audio_format=payload.audio_format,
        language_hint=payload.language_hint,
        text=payload.text,
        source_language=payload.source_language,
        target_language=payload.target_language,
        generate_tts=payload.generate_tts,
        voice_gender=payload.voice_gender,
        tts_audio_format=payload.tts_audio_format,
        consent_confirmed=payload.consent_confirmed,
        reply_to_id=payload.reply_to_id,
    )
    return VoiceWorkflowResponse(**res)


# -----------------------------------------------------------------------------
# 8. Real-Time Communication WebSocket Endpoint
# -----------------------------------------------------------------------------

@router.websocket("/ws")
async def voice_websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Authenticated WebSocket endpoint for real-time multilingual messaging notifications and read receipts.
    Connects clients via JWT token parameter (`ws://.../api/v1/voice/ws?token=<jwt>`).
    """
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    user_id_str = payload.get("sub")
    try:
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    user = db.query(User).filter(User.id == user_id, User.is_active.is_(True)).first()
    if not user:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await connection_manager.connect(user_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        connection_manager.disconnect(user_id, websocket)
