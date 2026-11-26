from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class VoiceConsent(Base):
    __tablename__ = "voice_consents"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    consent_granted = Column(Boolean, default=False, nullable=False)
    audio_retention_permitted = Column(Boolean, default=False, nullable=False)
    privacy_policy_accepted = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    user = relationship("User", back_populates="voice_consent")


class VoiceMessageLog(Base):
    __tablename__ = "voice_message_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    sender_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    recipient_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    source_language = Column(String(20), nullable=False)
    target_language = Column(String(20), nullable=False)
    original_text = Column(Text, nullable=False)
    translated_text = Column(Text, nullable=True)

    is_read = Column(Boolean, default=False, nullable=False, index=True)
    read_at = Column(DateTime(timezone=True), nullable=True)
    delivery_status = Column(String(50), default="delivered", nullable=False)  # 'sent', 'delivered', 'read', 'failed'
    translation_status = Column(String(50), default="none", nullable=False)  # 'none', 'completed', 'uncertain', 'failed', 'not_needed'
    is_uncertain = Column(Boolean, default=False, nullable=False)
    reply_to_id = Column(Integer, ForeignKey("voice_message_logs.id", ondelete="SET NULL"), nullable=True, index=True)
    audio_payload = Column(Text, nullable=True)
    audio_format = Column(String(50), nullable=True)

    consent_confirmed = Column(Boolean, default=True, nullable=False)
    stt_provider = Column(String(50), default="mock_development", nullable=False)
    translation_provider = Column(String(50), default="mock_development", nullable=False)
    tts_provider = Column(String(50), default="mock_development", nullable=False)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    sender = relationship("User", foreign_keys=[sender_id], back_populates="sent_voice_messages")
    recipient = relationship("User", foreign_keys=[recipient_id], back_populates="received_voice_messages")
    reply_to = relationship("VoiceMessageLog", remote_side=[id], backref="replies")


class VoiceAuditLog(Base):
    __tablename__ = "voice_audit_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    operation_type = Column(String(50), nullable=False)  # 'stt', 'translation', 'tts', 'consent_update', 'command'
    detected_language = Column(String(20), nullable=True)
    input_character_count = Column(Integer, default=0, nullable=False)
    output_character_count = Column(Integer, default=0, nullable=False)
    is_mock = Column(Boolean, default=True, nullable=False)
    provider = Column(String(50), default="mock_development", nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
