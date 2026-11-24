from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class EmergencyAlert(Base):
    __tablename__ = "emergency_alerts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patient_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    device_uuid = Column(String(100), nullable=True, index=True)
    
    # Alert source & details
    alert_type = Column(String(50), nullable=False)  # 'manual_sos', 'fall_detection', 'not_okay_assistance', 'vital_anomaly', 'voice_sos'
    severity = Column(String(20), default="critical", nullable=False)  # 'critical', 'high', 'moderate'
    status = Column(String(50), default="triggered", nullable=False, index=True)  # 'triggered', 'escalating', 'acknowledged', 'rejected', 'resolved', 'timeout_exhausted'
    current_escalation_tier = Column(Integer, default=1, nullable=False)
    
    # Location coordinates at time of alert
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    location_accuracy = Column(Float, nullable=True)
    
    # Message / Voice transcription
    assistance_message = Column(Text, nullable=True)  # User message for "I'm Not Okay"
    voice_transcript = Column(Text, nullable=True)
    detected_language = Column(String(20), nullable=True)
    translated_summary = Column(Text, nullable=True)
    
    # Acknowledgment & resolution
    acknowledged_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    rejected_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    rejected_at = Column(DateTime(timezone=True), nullable=True)
    rejection_reason = Column(Text, nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolution_notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    patient = relationship("PatientProfile", back_populates="emergency_alerts")
    acknowledged_by = relationship("User", foreign_keys=[acknowledged_by_id])
    rejected_by = relationship("User", foreign_keys=[rejected_by_id])
    audit_logs = relationship(
        "EscalationAuditLog",
        back_populates="alert",
        cascade="all, delete-orphan",
        order_by="EscalationAuditLog.sent_at.asc()"
    )


class EscalationAuditLog(Base):
    __tablename__ = "escalation_audit_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    alert_id = Column(Integer, ForeignKey("emergency_alerts.id", ondelete="CASCADE"), nullable=False, index=True)
    tier = Column(Integer, nullable=False)
    notified_caregiver_id = Column(Integer, ForeignKey("caregiver_profiles.id", ondelete="SET NULL"), nullable=True)
    notification_channel = Column(String(50), default="system", nullable=False)  # 'push', 'sms', 'email', 'system'
    provider = Column(String(50), default="development_mock", nullable=False)  # 'development_mock', 'fcm', 'twilio', 'smtp'
    recipient_address = Column(String(255), nullable=True)
    status = Column(String(50), default="dispatched_mock", nullable=False)  # 'dispatched_mock', 'delivered', 'failed', 'retry_pending'
    message_payload = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    sent_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    alert = relationship("EmergencyAlert", back_populates="audit_logs")
    caregiver = relationship("CaregiverProfile")
