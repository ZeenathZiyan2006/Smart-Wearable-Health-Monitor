from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class NovaWellbeingLog(Base):
    """
    Stores wellbeing check-ins for Patients and Caregivers.
    Caregiver wellbeing records are strictly isolated (is_caregiver_wellbeing=True)
    and kept completely separate from patient clinical records.
    """
    __tablename__ = "nova_wellbeing_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(50), nullable=False)  # 'patient', 'family', 'caregiver', 'doctor', 'emergency'
    target_patient_id = Column(Integer, ForeignKey("patient_profiles.id", ondelete="SET NULL"), nullable=True, index=True)
    
    mood_type = Column(String(50), nullable=False)  # 'calm', 'happy', 'tired', 'stressed', 'pain', 'lonely', 'routine_fatigue'
    notes = Column(Text, nullable=True)
    is_caregiver_wellbeing = Column(Boolean, default=False, nullable=False, index=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", foreign_keys=[user_id])
    target_patient = relationship("PatientProfile", foreign_keys=[target_patient_id])


class NovaAuditActionLog(Base):
    """
    Audit log for sensitive actions triggered or prepared via Nova
    (e.g. SOS escalation, direct phone dialing, family messaging, clinical note drafting).
    """
    __tablename__ = "nova_audit_actions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(50), nullable=False)
    action_type = Column(String(100), nullable=False, index=True)  # 'sos_triggered', 'phone_call_initiated', 'message_dispatched', 'clinical_review'
    target_patient_id = Column(Integer, ForeignKey("patient_profiles.id", ondelete="SET NULL"), nullable=True, index=True)
    
    status = Column(String(50), default="completed", nullable=False)  # 'initiated', 'completed', 'blocked_unauthorized', 'declined'
    details = Column(Text, nullable=True)
    client_ip = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", foreign_keys=[user_id])
    target_patient = relationship("PatientProfile", foreign_keys=[target_patient_id])
