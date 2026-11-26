from datetime import datetime, timezone
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class HealthTelemetry(Base):
    __tablename__ = "health_telemetry"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patient_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    device_uuid = Column(String(100), nullable=True, index=True)
    
    # Vital signs
    heart_rate = Column(Float, nullable=True)                  # Beats per minute
    spo2 = Column(Float, nullable=True)                        # Blood Oxygen Percentage (0-100)
    temperature = Column(Float, nullable=True)                 # Body temperature value
    temperature_unit = Column(String(10), default="C", nullable=False) # 'C' or 'F'
    
    # Activity, Sleep & Movement
    step_count = Column(Integer, default=0, nullable=False)
    activity_type = Column(String(50), default="resting", nullable=False)  # 'resting', 'walking', 'active'
    sleep_duration_minutes = Column(Integer, nullable=True)    # Tracked sleep duration in minutes
    
    # Accelerometer (MPU6050) & Fall status
    fall_detected = Column(Boolean, default=False, nullable=False)
    accelerometer_x = Column(Float, nullable=True)             # X-axis acceleration in g / m/s^2
    accelerometer_y = Column(Float, nullable=True)             # Y-axis acceleration
    accelerometer_z = Column(Float, nullable=True)             # Z-axis acceleration
    
        # Extended Vital Signs & Metrics
    blood_pressure_sys = Column(Float, nullable=True)          # Systolic blood pressure in mmHg
    blood_pressure_dia = Column(Float, nullable=True)          # Diastolic blood pressure in mmHg
    respiratory_rate = Column(Float, nullable=True)            # Breaths per minute
    calories_burned = Column(Float, nullable=True)             # Calories burned
    sleep_stage = Column(String(50), nullable=True)            # 'deep', 'light', 'rem', 'awake'
    
    # Hardware Telemetry
    battery_percentage = Column(Float, nullable=True)          # 0 - 100%
    
    # AI Analytics flags
    is_anomalous = Column(Boolean, default=False, nullable=False, index=True)
    anomaly_score = Column(Float, nullable=True)
    anomaly_reason = Column(Text, nullable=True)
    
    # Timestamps (always stored in UTC)
    recorded_at = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        UniqueConstraint("patient_id", "recorded_at", name="uq_health_telemetry_patient_timestamp"),
    )

    patient = relationship("PatientProfile", back_populates="health_readings")


class MedicalReport(Base):
    __tablename__ = "medical_reports"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patient_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    doctor_name = Column(String(100), default="Dr. Sunita Rao, MD", nullable=False)
    report_type = Column(String(100), default="Biometric Health Assessment", nullable=False)
    title = Column(String(255), nullable=False)
    summary = Column(Text, nullable=False)
    observations = Column(Text, nullable=True)
    recommendations = Column(Text, nullable=True)
    report_date = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    patient = relationship("PatientProfile", back_populates="medical_reports")


class PatientMedicine(Base):
    __tablename__ = "patient_medicines"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patient_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    medicine_name = Column(String(200), nullable=False)
    dosage = Column(String(100), nullable=False)              # e.g., '500 mg', '1 tablet'
    frequency = Column(String(100), nullable=False)           # 'Once daily', 'Twice daily', 'Thrice daily'
    scheduled_times = Column(String(200), nullable=False)     # JSON/comma-separated: '08:00,20:00'
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=True)
    expiry_date = Column(DateTime(timezone=True), nullable=True)
    total_quantity = Column(Integer, default=30, nullable=False)
    remaining_quantity = Column(Integer, default=30, nullable=False)
    medicine_status = Column(String(50), default="active", nullable=False) # 'active', 'discontinued', 'completed'
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    patient = relationship("PatientProfile")
    intake_logs = relationship("MedicineIntakeLog", back_populates="medicine", cascade="all, delete-orphan")


class MedicineIntakeLog(Base):
    __tablename__ = "medicine_intake_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    medicine_id = Column(Integer, ForeignKey("patient_medicines.id", ondelete="CASCADE"), nullable=False, index=True)
    patient_id = Column(Integer, ForeignKey("patient_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    scheduled_time = Column(DateTime(timezone=True), nullable=False)
    action_time = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    status = Column(String(50), default="taken", nullable=False)  # 'taken', 'skipped', 'missed'
    notes = Column(Text, nullable=True)

    medicine = relationship("PatientMedicine", back_populates="intake_logs")
    patient = relationship("PatientProfile")


class PatientReminder(Base):
    __tablename__ = "patient_reminders"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patient_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    reminder_type = Column(String(50), default="medicine", nullable=False)  # 'medicine', 'sleep', 'hydration', 'appointment'
    reminder_time = Column(String(50), nullable=False)        # '08:00' or ISO timestamp
    is_enabled = Column(Boolean, default=True, nullable=False)
    recurring_days = Column(String(100), default="Daily", nullable=False)  # 'Daily', 'Mon,Wed,Fri'
    alarm_tone = Column(String(100), default="chime_gentle", nullable=False)
    volume = Column(Integer, default=80, nullable=False)       # 0 - 100
    vibration_enabled = Column(Boolean, default=True, nullable=False)
    snooze_interval_minutes = Column(Integer, default=10, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    patient = relationship("PatientProfile")


class DoctorAppointment(Base):
    __tablename__ = "doctor_appointments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patient_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    doctor_name = Column(String(150), nullable=False)
    specialization = Column(String(150), default="Cardiologist", nullable=False)
    hospital_name = Column(String(200), default="PulseGuardian Heart Center", nullable=False)
    phone_number = Column(String(50), nullable=True)
    appointment_date = Column(DateTime(timezone=True), nullable=False)
    status = Column(String(50), default="confirmed", nullable=False)  # 'confirmed', 'completed', 'rescheduled', 'cancelled'
    reason = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    patient = relationship("PatientProfile")


class PatientMedicalCondition(Base):
    __tablename__ = "patient_medical_conditions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patient_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    condition_name = Column(String(200), nullable=False)
    diagnosed_date = Column(DateTime(timezone=True), nullable=True)
    severity = Column(String(50), default="moderate", nullable=False)  # 'mild', 'moderate', 'severe'
    status = Column(String(50), default="active", nullable=False)      # 'active', 'managed', 'resolved'
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    patient = relationship("PatientProfile")


class PatientAllergy(Base):
    __tablename__ = "patient_allergies"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patient_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    allergen = Column(String(200), nullable=False)            # e.g., 'Penicillin', 'Peanuts', 'Latex'
    reaction = Column(String(200), nullable=True)             # e.g., 'Rash', 'Anaphylaxis', 'Swelling'
    severity = Column(String(50), default="moderate", nullable=False) # 'mild', 'moderate', 'severe'
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    patient = relationship("PatientProfile")


class PatientHydrationLog(Base):
    __tablename__ = "patient_hydration_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patient_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    intake_ml = Column(Integer, default=250, nullable=False)  # Intake in milliliters (e.g. 250ml glass)
    logged_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    patient = relationship("PatientProfile")
