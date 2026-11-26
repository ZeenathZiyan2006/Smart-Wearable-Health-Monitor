import base64
from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional, Set
from fastapi import HTTPException, WebSocket, status
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.user import CaregiverProfile, PatientCaregiverAssociation, PatientProfile, User, UserRole
from app.models.voice import VoiceAuditLog, VoiceConsent, VoiceMessageLog
from app.schemas.voice import (
    MOCK_TRANSLATION_DISCLAIMER,
    REAL_STT_DISCLAIMER,
    REAL_TRANSLATION_DISCLAIMER,
    REAL_TTS_DISCLAIMER,
    SUPPORTED_AUDIO_MIME_TYPES,
    SUPPORTED_LANGUAGE_CODES,
    ConversationPartnerSummary,
)
from app.services.voice.adapters import (
    get_stt_adapter,
    get_translation_adapter,
    get_tts_adapter,
)
from app.services.voice.adapters.translation_adapter import detect_script_language
from app.services.voice.audio_validator import inspect_audio_duration

logger = logging.getLogger("pulseguardian.voice.messaging")


# -----------------------------------------------------------------------------
# Real-Time WebSocket Connection Manager
# -----------------------------------------------------------------------------
class VoiceConnectionManager:
    """
    In-memory WebSocket connection manager for active voice and messaging sessions.
    Broadcasting message events and read receipts to authenticated connected clients.
    """

    def __init__(self):
        self._active_connections: Dict[int, Set[WebSocket]] = {}

    async def connect(self, user_id: int, websocket: WebSocket) -> None:
        await websocket.accept()
        if user_id not in self._active_connections:
            self._active_connections[user_id] = set()
        self._active_connections[user_id].add(websocket)
        logger.info(f"WebSocket client connected for user_id={user_id}")

    def disconnect(self, user_id: int, websocket: WebSocket) -> None:
        if user_id in self._active_connections:
            self._active_connections[user_id].discard(websocket)
            if not self._active_connections[user_id]:
                del self._active_connections[user_id]
        logger.info(f"WebSocket client disconnected for user_id={user_id}")

    async def broadcast_to_user(self, user_id: int, message: Dict[str, Any]) -> None:
        if user_id in self._active_connections:
            stale_sockets = []
            for ws in self._active_connections[user_id]:
                try:
                    await ws.send_json(message)
                except Exception as exc:
                    logger.warning(f"Failed to deliver WebSocket message to user_id={user_id}: {exc}")
                    stale_sockets.append(ws)
            for ws in stale_sockets:
                self.disconnect(user_id, ws)


# Global connection manager singleton
connection_manager = VoiceConnectionManager()


# -----------------------------------------------------------------------------
# Authorization & Consent Helper Functions
# -----------------------------------------------------------------------------
def check_voice_consent(db: Session, user_id: int, request_consent_confirmed: bool) -> bool:
    """
    Checks affirmative consent for voice processing and AI translation.
    Validates either explicit per-request confirmation or persistent active consent preference.
    """
    if not settings.VOICE_ENABLE_CONSENT_ENFORCEMENT:
        return True

    if request_consent_confirmed:
        return True

    consent_record = db.query(VoiceConsent).filter(VoiceConsent.user_id == user_id).first()
    if consent_record and consent_record.consent_granted:
        return True

    return False


def validate_patient_caregiver_relationship(db: Session, user1_id: int, user2_id: int) -> bool:
    """
    Verifies that user1 and user2 share an authorized PatientCaregiverAssociation.
    A patient can only communicate with assigned caregivers; a caregiver only with assigned patients.
    Prevents IDOR and unauthorized cross-patient data access.
    """
    if user1_id == user2_id:
        return False

    u1 = db.query(User).filter(User.id == user1_id).first()
    u2 = db.query(User).filter(User.id == user2_id).first()
    if not u1 or not u2:
        return False

    # Admins have supervisory access if needed, but patient-caregiver association is standard
    if u1.role == UserRole.ADMIN.value or u2.role == UserRole.ADMIN.value:
        return True

    # Case A: user1 is patient, user2 is caregiver
    if u1.role == UserRole.PATIENT.value and u2.role == UserRole.CAREGIVER.value:
        p_profile = db.query(PatientProfile).filter(PatientProfile.user_id == user1_id).first()
        c_profile = db.query(CaregiverProfile).filter(CaregiverProfile.user_id == user2_id).first()
        if not p_profile or not c_profile:
            return False
        assoc = db.query(PatientCaregiverAssociation).filter(
            PatientCaregiverAssociation.patient_id == p_profile.id,
            PatientCaregiverAssociation.caregiver_id == c_profile.id
        ).first()
        return assoc is not None

    # Case B: user1 is caregiver, user2 is patient
    if u1.role == UserRole.CAREGIVER.value and u2.role == UserRole.PATIENT.value:
        c_profile = db.query(CaregiverProfile).filter(CaregiverProfile.user_id == user1_id).first()
        p_profile = db.query(PatientProfile).filter(PatientProfile.user_id == user2_id).first()
        if not c_profile or not p_profile:
            return False
        assoc = db.query(PatientCaregiverAssociation).filter(
            PatientCaregiverAssociation.caregiver_id == c_profile.id,
            PatientCaregiverAssociation.patient_id == p_profile.id
        ).first()
        return assoc is not None

    return False


def get_authorized_partner_ids(db: Session, user: User) -> List[int]:
    """Retrieves all User IDs authorized to communicate with the given user."""
    if user.role == UserRole.PATIENT.value:
        p_profile = db.query(PatientProfile).filter(PatientProfile.user_id == user.id).first()
        if not p_profile:
            return []
        assocs = db.query(PatientCaregiverAssociation).filter(
            PatientCaregiverAssociation.patient_id == p_profile.id
        ).all()
        caregiver_profile_ids = [a.caregiver_id for a in assocs]
        c_profiles = db.query(CaregiverProfile).filter(CaregiverProfile.id.in_(caregiver_profile_ids)).all()
        return [c.user_id for c in c_profiles]

    elif user.role == UserRole.CAREGIVER.value:
        c_profile = db.query(CaregiverProfile).filter(CaregiverProfile.user_id == user.id).first()
        if not c_profile:
            return []
        assocs = db.query(PatientCaregiverAssociation).filter(
            PatientCaregiverAssociation.caregiver_id == c_profile.id
        ).all()
        patient_profile_ids = [a.patient_id for a in assocs]
        p_profiles = db.query(PatientProfile).filter(PatientProfile.id.in_(patient_profile_ids)).all()
        return [p.user_id for p in p_profiles]

    return []


# -----------------------------------------------------------------------------
# Messaging Business Logic
# -----------------------------------------------------------------------------
def send_multilingual_message(
    db: Session,
    sender: User,
    recipient_id: int,
    text: str,
    source_language: Optional[str] = None,
    target_language: Optional[str] = None,
    auto_translate: bool = True,
    consent_confirmed: bool = True,
    reply_to_id: Optional[int] = None,
    audio_payload: Optional[str] = None,
    audio_format: Optional[str] = None,
    stt_provider: str = "none",
) -> VoiceMessageLog:
    """
    Sends a multilingual message from an authorized patient or caregiver.
    Strictly verifies relationship authorization and affirmative consent.
    Preserves original text and translated text separately without destructive replacement.
    """
    if not validate_patient_caregiver_relationship(db, sender.id, recipient_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Communication is only permitted between associated patients and caregivers."
        )

    recipient = db.query(User).filter(User.id == recipient_id, User.is_active.is_(True)).first()
    if not recipient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recipient user with ID {recipient_id} not found or inactive."
        )

    cleaned_text = (text or "").strip()
    if not cleaned_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message text cannot be empty."
        )

    if len(cleaned_text) > settings.VOICE_MAX_TRANSLATION_CHARS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Message text exceeds maximum limit of {settings.VOICE_MAX_TRANSLATION_CHARS} characters."
        )

    # Validate parent message if replying
    if reply_to_id is not None:
        parent_msg = db.query(VoiceMessageLog).filter(VoiceMessageLog.id == reply_to_id).first()
        if not parent_msg or (parent_msg.sender_id != recipient_id and parent_msg.recipient_id != recipient_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid reply_to_id {reply_to_id}: Message does not belong to this conversation."
            )

    # Determine source language
    if source_language:
        src_lang = source_language.lower().strip()
        if src_lang not in SUPPORTED_LANGUAGE_CODES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported source language code '{source_language}'. Supported: {', '.join(SUPPORTED_LANGUAGE_CODES)}"
            )
    else:
        detected_src, _ = detect_script_language(cleaned_text)
        src_lang = detected_src if detected_src and detected_src != "uncertain" else (sender.preferred_language or "en")

    # Determine target language
    if target_language:
        tgt_lang = target_language.lower().strip()
        if tgt_lang not in SUPPORTED_LANGUAGE_CODES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported target language code '{target_language}'. Supported: {', '.join(SUPPORTED_LANGUAGE_CODES)}"
            )
    else:
        tgt_lang = recipient.preferred_language or "en"

    # Translation execution
    translated_text = None
    translation_status = "none"
    is_uncertain = False
    translation_provider = "none"

    if auto_translate and src_lang != tgt_lang:
        # Check affirmative consent before AI processing
        if not check_voice_consent(db, sender.id, consent_confirmed):
            translation_status = "consent_required"
        else:
            translator = get_translation_adapter()
            try:
                res = translator.translate(
                    text=cleaned_text,
                    source_language=src_lang,
                    target_language=tgt_lang
                )
                translated_text = res.translated_text
                translation_status = "completed" if not res.uncertain_translation else "uncertain"
                is_uncertain = res.uncertain_translation
                translation_provider = res.provider
            except Exception as exc:
                logger.error(f"Automatic translation failed for message: {exc.__class__.__name__}")
                translation_status = "failed"
                translation_provider = getattr(translator, "provider", "unknown")
    elif src_lang == tgt_lang:
        translation_status = "not_needed"
        translated_text = cleaned_text

    # Persist message
    msg = VoiceMessageLog(
        sender_id=sender.id,
        recipient_id=recipient.id,
        source_language=src_lang,
        target_language=tgt_lang,
        original_text=cleaned_text,
        translated_text=translated_text,
        is_read=False,
        read_at=None,
        delivery_status="delivered",
        translation_status=translation_status,
        is_uncertain=is_uncertain,
        reply_to_id=reply_to_id,
        audio_payload=audio_payload,
        audio_format=audio_format,
        consent_confirmed=consent_confirmed,
        stt_provider=stt_provider,
        translation_provider=translation_provider,
        tts_provider="none",
        created_at=datetime.now(timezone.utc)
    )
    db.add(msg)
    db.flush()

    # Ephemeral audit log (metadata only; never stores sensitive patient text)
    audit = VoiceAuditLog(
        user_id=sender.id,
        operation_type="message_sent",
        detected_language=src_lang,
        input_character_count=len(cleaned_text),
        output_character_count=len(translated_text) if translated_text else 0,
        is_mock=(translation_provider == "mock_development"),
        provider=translation_provider,
        created_at=datetime.now(timezone.utc)
    )
    db.add(audit)
    db.commit()
    db.refresh(msg)

    return msg


def get_conversation_messages(
    db: Session,
    user: User,
    partner_id: int,
    limit: int = 50,
    offset: int = 0,
    since: Optional[datetime] = None
) -> List[VoiceMessageLog]:
    """Retrieves conversation message history between user and authorized partner."""
    if not validate_patient_caregiver_relationship(db, user.id, partner_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: You are not authorized to view messages with this user."
        )

    query = db.query(VoiceMessageLog).filter(
        or_(
            and_(VoiceMessageLog.sender_id == user.id, VoiceMessageLog.recipient_id == partner_id),
            and_(VoiceMessageLog.sender_id == partner_id, VoiceMessageLog.recipient_id == user.id),
        )
    )

    if since:
        query = query.filter(VoiceMessageLog.created_at > since)

    return query.order_by(VoiceMessageLog.created_at.asc()).offset(offset).limit(limit).all()


def get_conversations_summary(db: Session, user: User) -> List[ConversationPartnerSummary]:
    """Returns conversation summaries for all authorized partners of the given user."""
    partner_ids = get_authorized_partner_ids(db, user)
    if not partner_ids:
        return []

    summaries = []
    partners = db.query(User).filter(User.id.in_(partner_ids), User.is_active.is_(True)).all()

    for p in partners:
        # Count unread messages from this partner
        unread_count = db.query(VoiceMessageLog).filter(
            VoiceMessageLog.sender_id == p.id,
            VoiceMessageLog.recipient_id == user.id,
            VoiceMessageLog.is_read.is_(False)
        ).count()

        # Find latest message in conversation
        latest_msg = db.query(VoiceMessageLog).filter(
            or_(
                and_(VoiceMessageLog.sender_id == user.id, VoiceMessageLog.recipient_id == p.id),
                and_(VoiceMessageLog.sender_id == p.id, VoiceMessageLog.recipient_id == user.id),
            )
        ).order_by(VoiceMessageLog.created_at.desc()).first()

        snippet = None
        last_at = None
        if latest_msg:
            last_at = latest_msg.created_at
            snippet = latest_msg.original_text[:60] + "..." if len(latest_msg.original_text) > 60 else latest_msg.original_text

        # Determine relationship type
        rel_type = None
        if p.role == UserRole.CAREGIVER.value and p.caregiver_profile:
            rel_type = p.caregiver_profile.relationship_type

        summaries.append(
            ConversationPartnerSummary(
                partner_id=p.id,
                full_name=p.full_name,
                role=p.role,
                preferred_language=p.preferred_language or "en",
                relationship_type=rel_type,
                unread_count=unread_count,
                last_message_at=last_at,
                last_message_snippet=snippet,
            )
        )

    # Sort conversations by latest message timestamp
    summaries.sort(key=lambda s: s.last_message_at or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
    return summaries


def get_message_by_id(db: Session, message_id: int, user: User) -> VoiceMessageLog:
    """Retrieves message details ensuring strict ownership / conversation authorization."""
    msg = db.query(VoiceMessageLog).filter(VoiceMessageLog.id == message_id).first()
    if not msg:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Message with ID {message_id} not found."
        )

    if msg.sender_id != user.id and msg.recipient_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: You are not authorized to view this message."
        )

    return msg


def mark_message_as_read(db: Session, message_id: int, user: User) -> VoiceMessageLog:
    """Marks a message as read by the intended recipient."""
    msg = get_message_by_id(db, message_id, user)
    if msg.recipient_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only the recipient of a message can mark it as read."
        )

    if not msg.is_read:
        msg.is_read = True
        msg.read_at = datetime.now(timezone.utc)
        msg.delivery_status = "read"
        db.commit()
        db.refresh(msg)

    return msg


def mark_all_messages_read_in_conversation(db: Session, partner_id: int, user: User) -> int:
    """Marks all unread messages from partner to user as read."""
    if not validate_patient_caregiver_relationship(db, user.id, partner_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: You are not authorized to update messages with this user."
        )

    now = datetime.now(timezone.utc)
    updated_count = db.query(VoiceMessageLog).filter(
        VoiceMessageLog.sender_id == partner_id,
        VoiceMessageLog.recipient_id == user.id,
        VoiceMessageLog.is_read.is_(False)
    ).update(
        {"is_read": True, "read_at": now, "delivery_status": "read"},
        synchronize_session=False
    )
    db.commit()
    return updated_count


def translate_message_on_demand(
    db: Session,
    message_id: int,
    user: User,
    target_language: Optional[str] = None,
    consent_confirmed: bool = True
) -> VoiceMessageLog:
    """Translates an existing message on demand for the viewing participant."""
    msg = get_message_by_id(db, message_id, user)

    if not check_voice_consent(db, user.id, consent_confirmed):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Consent required: Affirmative user authorization is mandatory before translating message content."
        )

    tgt = (target_language or user.preferred_language or "en").lower().strip()
    if tgt not in SUPPORTED_LANGUAGE_CODES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported target language '{target_language}'. Supported: {', '.join(SUPPORTED_LANGUAGE_CODES)}"
        )

    translator = get_translation_adapter()
    try:
        res = translator.translate(
            text=msg.original_text,
            source_language=msg.source_language,
            target_language=tgt
        )
    except ValueError as val_err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(val_err))
    except TimeoutError as timeout_err:
        raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail=str(timeout_err))
    except ConnectionError as conn_err:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(conn_err))
    except RuntimeError as rt_err:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(rt_err))

    msg.translated_text = res.translated_text
    msg.target_language = tgt
    msg.translation_status = "completed" if not res.uncertain_translation else "uncertain"
    msg.is_uncertain = res.uncertain_translation
    msg.translation_provider = res.provider

    audit = VoiceAuditLog(
        user_id=user.id,
        operation_type="message_translation_on_demand",
        detected_language=msg.source_language,
        input_character_count=len(msg.original_text),
        output_character_count=len(res.translated_text),
        is_mock=res.is_mock,
        provider=res.provider,
        created_at=datetime.now(timezone.utc)
    )
    db.add(audit)
    db.commit()
    db.refresh(msg)
    return msg


def synthesize_message_speech_on_demand(
    db: Session,
    message_id: int,
    user: User,
    language_code: Optional[str] = None,
    voice_gender: str = "neutral",
    audio_format: str = "audio/mp3",
    consent_confirmed: bool = True
) -> Dict[str, Any]:
    """Synthesizes speech audio for an existing message on demand."""
    msg = get_message_by_id(db, message_id, user)

    if not check_voice_consent(db, user.id, consent_confirmed):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Consent required: Affirmative user authorization is mandatory before generating synthesized audio."
        )

    # Determine text and language to synthesize
    lang = (language_code or msg.target_language or msg.source_language or "en").lower().strip()
    if lang not in SUPPORTED_LANGUAGE_CODES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported language code '{language_code}'. Supported: {', '.join(SUPPORTED_LANGUAGE_CODES)}"
        )

    if lang == msg.target_language and msg.translated_text:
        text_to_speak = msg.translated_text
    else:
        text_to_speak = msg.original_text

    tts = get_tts_adapter()
    try:
        result = tts.synthesize(
            text=text_to_speak,
            language_code=lang,
            voice_gender=voice_gender,
            audio_format=audio_format
        )
    except ValueError as val_err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(val_err))
    except TimeoutError as timeout_err:
        raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail=str(timeout_err))
    except ConnectionError as conn_err:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(conn_err))
    except RuntimeError as rt_err:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(rt_err))

    audit = VoiceAuditLog(
        user_id=user.id,
        operation_type="message_tts_on_demand",
        detected_language=lang,
        input_character_count=len(text_to_speak),
        output_character_count=len(result.audio_payload),
        is_mock=result.is_mock,
        provider=result.provider,
        created_at=datetime.now(timezone.utc)
    )
    db.add(audit)
    db.commit()

    return {
        "message_id": msg.id,
        "language_code": result.language_code,
        "audio_payload": result.audio_payload,
        "audio_format": result.audio_format,
        "is_mock": result.is_mock,
        "is_playable": result.is_playable,
        "provider": result.provider,
        "disclaimer": result.disclaimer,
    }


# -----------------------------------------------------------------------------
# End-to-End Voice Message Workflow Implementation
# -----------------------------------------------------------------------------
def execute_voice_workflow(
    db: Session,
    sender: User,
    recipient_id: int,
    audio_base64: Optional[str] = None,
    audio_format: Optional[str] = "audio/wav",
    language_hint: Optional[str] = None,
    text: Optional[str] = None,
    source_language: Optional[str] = None,
    target_language: Optional[str] = None,
    generate_tts: bool = False,
    voice_gender: str = "neutral",
    tts_audio_format: str = "audio/mp3",
    consent_confirmed: bool = True,
    reply_to_id: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Executes the comprehensive multilingual voice workflow end-to-end:
    Patient speech -> validation -> STT -> language detection -> translation -> persistence -> optional TTS.
    Also handles text-only workflows with equal consistency and explicit stage statuses.
    """
    # Stage 1: Authorization & Consent Validation
    if not validate_patient_caregiver_relationship(db, sender.id, recipient_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Communication is only permitted between associated patients and caregivers."
        )

    if not check_voice_consent(db, sender.id, consent_confirmed):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Consent required: Affirmative user authorization is mandatory before processing voice/speech workflows."
        )

    recipient = db.query(User).filter(User.id == recipient_id, User.is_active.is_(True)).first()
    if not recipient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recipient user with ID {recipient_id} not found."
        )

    stage_statuses = {
        "audio_validation": "skipped",
        "stt_transcription": "skipped",
        "language_detection": "skipped",
        "translation": "skipped",
        "tts_synthesis": "skipped",
    }
    disclaimers = []
    uncertain_speech = False
    uncertain_translation = False
    stt_provider_name = "none"
    translation_provider_name = "none"
    tts_provider_name = "none"

    original_text = ""
    effective_src_lang = "en"

    # Stage 2: Audio Validation & STT Transcription (if audio provided)
    if audio_base64 and audio_base64.strip():
        stage_statuses["audio_validation"] = "in_progress"
        fmt = (audio_format or "audio/wav").lower().strip()
        if fmt not in SUPPORTED_AUDIO_MIME_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported audio MIME type '{audio_format}'. Supported: {', '.join(SUPPORTED_AUDIO_MIME_TYPES)}"
            )

        try:
            audio_bytes = base64.b64decode(audio_base64.strip(), validate=True)
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

        if len(audio_bytes) > settings.VOICE_MAX_AUDIO_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Audio payload size ({len(audio_bytes)} bytes) exceeds the maximum allowed limit of {settings.VOICE_MAX_AUDIO_SIZE_BYTES} bytes."
            )

        # Inspect duration pre-flight
        try:
            duration_sec = inspect_audio_duration(audio_bytes, fmt)
        except ValueError as val_err:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Audio validation failed: {str(val_err)}")
        except Exception:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not parse audio duration.")

        if duration_sec > settings.VOICE_MAX_AUDIO_DURATION_SECONDS:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Audio duration ({duration_sec:.2f}s) exceeds maximum limit of {settings.VOICE_MAX_AUDIO_DURATION_SECONDS} seconds."
            )

        stage_statuses["audio_validation"] = "completed"

        # Execute STT transcription
        stage_statuses["stt_transcription"] = "in_progress"
        stt_adapter = get_stt_adapter()
        stt_res = stt_adapter.transcribe(
            audio_bytes=audio_bytes,
            content_type=fmt,
            hint_language=language_hint
        )
        original_text = stt_res.transcript
        effective_src_lang = stt_res.detected_language if stt_res.detected_language in SUPPORTED_LANGUAGE_CODES else "en"
        uncertain_speech = stt_res.uncertain_speech
        stt_provider_name = stt_res.provider
        stage_statuses["stt_transcription"] = "completed" if not uncertain_speech else "uncertain"
        disclaimers.append(stt_res.disclaimer)

    elif text and text.strip():
        # Text-only workflow branch
        original_text = text.strip()
        if len(original_text) > settings.VOICE_MAX_TRANSLATION_CHARS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Text length exceeds maximum allowed limit of {settings.VOICE_MAX_TRANSLATION_CHARS} characters."
            )

        if source_language:
            src = source_language.lower().strip()
            if src not in SUPPORTED_LANGUAGE_CODES:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unsupported source language code '{source_language}'."
                )
            effective_src_lang = src
        else:
            detected, is_unc = detect_script_language(original_text)
            effective_src_lang = detected if detected and detected != "uncertain" else (sender.preferred_language or "en")
            if is_unc:
                uncertain_speech = True

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Workflow requires either 'audio_base64' speech input or 'text' payload."
        )

    stage_statuses["language_detection"] = "completed" if not uncertain_speech else "uncertain"

    # Stage 3: Target Language Determination & Translation
    eff_tgt_lang = (target_language or recipient.preferred_language or "en").lower().strip()
    if eff_tgt_lang not in SUPPORTED_LANGUAGE_CODES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported target language '{target_language}'. Supported: {', '.join(SUPPORTED_LANGUAGE_CODES)}"
        )

    translated_text = None
    translation_status = "none"

    if effective_src_lang != eff_tgt_lang:
        stage_statuses["translation"] = "in_progress"
        translator = get_translation_adapter()
        try:
            trans_res = translator.translate(
                text=original_text,
                source_language=effective_src_lang,
                target_language=eff_tgt_lang
            )
            translated_text = trans_res.translated_text
            uncertain_translation = trans_res.uncertain_translation
            translation_status = "completed" if not uncertain_translation else "uncertain"
            stage_statuses["translation"] = translation_status
            translation_provider_name = trans_res.provider
            disclaimers.append(trans_res.disclaimer)
        except Exception as exc:
            logger.error(f"Workflow translation failed: {exc.__class__.__name__}")
            stage_statuses["translation"] = "failed"
            translation_status = "failed"
            translation_provider_name = getattr(translator, "provider", "unknown")
    else:
        stage_statuses["translation"] = "skipped"
        translation_status = "not_needed"
        translated_text = original_text

    # Stage 4: Optional Text-to-Speech Synthesis
    tts_b64 = None
    if generate_tts:
        stage_statuses["tts_synthesis"] = "in_progress"
        tts_lang = eff_tgt_lang if translated_text else effective_src_lang
        tts_text = translated_text if translated_text else original_text

        tts_adapter = get_tts_adapter()
        try:
            tts_res = tts_adapter.synthesize(
                text=tts_text,
                language_code=tts_lang,
                voice_gender=voice_gender,
                audio_format=tts_audio_format
            )
            tts_b64 = tts_res.audio_payload
            tts_provider_name = tts_res.provider
            stage_statuses["tts_synthesis"] = "completed"
            disclaimers.append(tts_res.disclaimer)
        except Exception as exc:
            logger.error(f"Workflow TTS synthesis failed: {exc.__class__.__name__}")
            stage_statuses["tts_synthesis"] = "failed"
            tts_provider_name = getattr(tts_adapter, "provider", "unknown")

    # Stage 5: Ephemeral / Message Persistence
    is_uncertain_overall = uncertain_speech or uncertain_translation

    msg = VoiceMessageLog(
        sender_id=sender.id,
        recipient_id=recipient.id,
        source_language=effective_src_lang,
        target_language=eff_tgt_lang,
        original_text=original_text,
        translated_text=translated_text,
        is_read=False,
        read_at=None,
        delivery_status="delivered",
        translation_status=translation_status,
        is_uncertain=is_uncertain_overall,
        reply_to_id=reply_to_id,
        audio_payload=tts_b64 if generate_tts else None,
        audio_format=tts_audio_format if generate_tts else None,
        consent_confirmed=consent_confirmed,
        stt_provider=stt_provider_name,
        translation_provider=translation_provider_name,
        tts_provider=tts_provider_name,
        created_at=datetime.now(timezone.utc)
    )
    db.add(msg)
    db.flush()

    audit = VoiceAuditLog(
        user_id=sender.id,
        operation_type="voice_workflow_dispatch",
        detected_language=effective_src_lang,
        input_character_count=len(original_text),
        output_character_count=len(translated_text) if translated_text else 0,
        is_mock=(stt_provider_name == "mock_development" or translation_provider_name == "mock_development"),
        provider=f"{stt_provider_name}+{translation_provider_name}",
        created_at=datetime.now(timezone.utc)
    )
    db.add(audit)
    db.commit()
    db.refresh(msg)

    return {
        "message_id": msg.id,
        "sender_id": sender.id,
        "recipient_id": recipient.id,
        "stage_statuses": stage_statuses,
        "source_language": effective_src_lang,
        "target_language": eff_tgt_lang,
        "original_text": original_text,
        "translated_text": translated_text,
        "uncertain_speech": uncertain_speech,
        "uncertain_translation": uncertain_translation,
        "is_uncertain": is_uncertain_overall,
        "audio_payload": tts_b64,
        "audio_format": tts_audio_format if generate_tts else None,
        "stt_provider": stt_provider_name,
        "translation_provider": translation_provider_name,
        "tts_provider": tts_provider_name,
        "disclaimers": disclaimers,
        "created_at": msg.created_at,
    }
