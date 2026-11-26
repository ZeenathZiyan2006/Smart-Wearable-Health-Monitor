from datetime import datetime, date, timezone
from enum import Enum
from typing import List, Optional
from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class UserRole(str, Enum):
    PATIENT = "patient"
    CAREGIVER = "caregiver"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), default=UserRole.PATIENT.value, nullable=False)
    phone_number = Column(String(50), nullable=True)
    preferred_language = Column(String(20), default="en", nullable=False)  # 'en', 'kn', 'hi', 'ml'
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # One-to-one profiles
    patient_profile = relationship("PatientProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    caregiver_profile = relationship("CaregiverProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    voice_consent = relationship("VoiceConsent", back_populates="user", uselist=False, cascade="all, delete-orphan")
    sent_voice_messages = relationship("VoiceMessageLog", foreign_keys="[VoiceMessageLog.sender_id]", back_populates="sender", cascade="all, delete-orphan")
    received_voice_messages = relationship("VoiceMessageLog", foreign_keys="[VoiceMessageLog.recipient_id]", back_populates="recipient", cascade="all, delete-orphan")


class PatientCaregiverAssociation(Base):
    __tablename__ = "patient_caregiver_associations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patient_profiles.id", ondelete="CASCADE"), nullable=False)
    caregiver_id = Column(Integer, ForeignKey("caregiver_profiles.id", ondelete="CASCADE"), nullable=False)
    is_primary = Column(Boolean, default=False, nullable=False)
    access_level = Column(String(50), default="full", nullable=False)  # 'full', 'read_only', 'emergency_only'
    escalation_tier = Column(Integer, default=1, nullable=False)  # 1 = primary, 2 = secondary, 3 = tertiary
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        UniqueConstraint("patient_id", "caregiver_id", name="uq_patient_caregiver"),
    )

    patient = relationship("PatientProfile", back_populates="caregiver_associations")
    caregiver = relationship("CaregiverProfile", back_populates="patient_associations")


class PatientProfile(Base):
    __tablename__ = "patient_profiles"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    date_of_birth = Column(Date, nullable=True)
    gender = Column(String(20), nullable=True)
    blood_group = Column(String(10), nullable=True)
    medical_history = Column(Text, nullable=True)
    emergency_contact_phone = Column(String(50), nullable=True)
    device_uuid = Column(String(100), unique=True, index=True, nullable=True)
    device_status = Column(String(50), default="offline", nullable=False)  # 'online', 'offline', 'syncing'
    last_sync_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    user = relationship("User", back_populates="patient_profile")
    caregiver_associations = relationship(
        "PatientCaregiverAssociation",
        back_populates="patient",
        cascade="all, delete-orphan"
    )
    health_readings = relationship("HealthTelemetry", back_populates="patient", cascade="all, delete-orphan")
    emergency_alerts = relationship("EmergencyAlert", back_populates="patient", cascade="all, delete-orphan")
    location_logs = relationship("LocationLog", back_populates="patient", cascade="all, delete-orphan")
    digital_twin = relationship("DigitalTwinBaseline", back_populates="patient", uselist=False, cascade="all, delete-orphan")
    drift_records = relationship("HealthDriftRecord", back_populates="patient", cascade="all, delete-orphan")



class CaregiverProfile(Base):
    __tablename__ = "caregiver_profiles"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    relationship_type = Column(String(50), default="Family", nullable=False)  # 'Family', 'Doctor', 'Nurse', 'Guardian'
    organization = Column(String(100), nullable=True)
    notification_preference = Column(String(50), default="all", nullable=False)  # 'push', 'sms', 'email', 'all'
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    user = relationship("User", back_populates="caregiver_profile")
    patient_associations = relationship(
        "PatientCaregiverAssociation",
        back_populates="caregiver",
        cascade="all, delete-orphan"
    )
