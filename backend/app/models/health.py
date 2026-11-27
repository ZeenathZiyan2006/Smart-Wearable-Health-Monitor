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


# =========================================================================
# MODULE 1: AI Early Warning Prediction Model
# =========================================================================
class EarlyWarningPrediction(Base):
    __tablename__ = "early_warning_predictions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patient_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    risk_level = Column(String(50), default="normal", nullable=False)  # 'normal', 'low', 'moderate', 'high'
    parameter_changed = Column(String(100), nullable=False)           # 'heart_rate', 'spo2', 'blood_pressure', 'temperature', 'activity', 'sleep'
    previous_value = Column(String(100), nullable=False)
    current_value = Column(String(100), nullable=False)
    observed_pattern = Column(Text, nullable=False)
    recommendation = Column(Text, nullable=False)
    alert_triggered = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    patient = relationship("PatientProfile")


# =========================================================================
# MODULE 2: Fall Detection Model
# =========================================================================
class FallEvent(Base):
    __tablename__ = "fall_events"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patient_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    device_uuid = Column(String(100), nullable=True)
    status = Column(String(50), default="pending_confirmation", nullable=False)  # 'pending_confirmation', 'confirmed_safe', 'help_requested', 'escalated_unresponsive'
    confidence_score = Column(Float, default=0.88, nullable=False)
    impact_g = Column(Float, default=3.2, nullable=False)
    orientation_change_deg = Column(Float, default=74.5, nullable=False)
    confirmation_timeout_sec = Column(Integer, default=30, nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    patient_response = Column(String(50), nullable=True)
    escalated_at = Column(DateTime(timezone=True), nullable=True)
    emergency_alert_id = Column(Integer, ForeignKey("emergency_alerts.id", ondelete="SET NULL"), nullable=True)
    recorded_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    patient = relationship("PatientProfile")


# =========================================================================
# MODULE 3: Abnormal Inactivity Detection Model
# =========================================================================
class InactivityEvent(Base):
    __tablename__ = "inactivity_events"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patient_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    device_uuid = Column(String(100), nullable=True)
    inactivity_duration_minutes = Column(Integer, nullable=False)
    threshold_minutes = Column(Integer, default=120, nullable=False)
    during_sleep_schedule = Column(Boolean, default=False, nullable=False)
    status = Column(String(50), default="warning_issued", nullable=False)  # 'warning_issued', 'confirmed_safe', 'escalated'
    patient_response = Column(String(50), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    recorded_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    patient = relationship("PatientProfile")


# =========================================================================
# MODULE 4: Voice Assistant Settings Model
# =========================================================================
class VoiceAssistantSetting(Base):
    __tablename__ = "voice_assistant_settings"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patient_profiles.id", ondelete="CASCADE"), unique=True, nullable=False)
    is_enabled = Column(Boolean, default=True, nullable=False)
    preferred_language = Column(String(20), default="en", nullable=False)  # 'en', 'kn', 'hi'
    voice_id = Column(String(50), default="natural_female", nullable=False)
    speech_speed = Column(Float, default=1.0, nullable=False)
    volume = Column(Float, default=0.9, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    patient = relationship("PatientProfile")


# =========================================================================
# MODULE 5: Nearest Hospital & Emergency Assistance Model
# =========================================================================
class HospitalEmergencySetting(Base):
    __tablename__ = "hospital_emergency_settings"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patient_profiles.id", ondelete="CASCADE"), unique=True, nullable=False)
    is_enabled = Column(Boolean, default=True, nullable=False)
    preferred_hospital_name = Column(String(200), default="Manipal Hospital & Emergency Center", nullable=False)
    preferred_hospital_phone = Column(String(50), default="+91 80 2502 4444", nullable=False)
    fixed_family_doctor_name = Column(String(150), default="Dr. Sunita Rao", nullable=False)
    fixed_family_doctor_phone = Column(String(50), default="+91 98450 12345", nullable=False)
    emergency_contact_phone = Column(String(50), default="112", nullable=False)
    location_sharing_permitted = Column(Boolean, default=True, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    patient = relationship("PatientProfile")


# =========================================================================
# MODULE 7: Emergency Medical QR Profile Model
# =========================================================================
class EmergencyQRProfile(Base):
    __tablename__ = "emergency_qr_profiles"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patient_profiles.id", ondelete="CASCADE"), unique=True, nullable=False)
    qr_token = Column(String(100), unique=True, index=True, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    blood_group = Column(String(20), default="O+", nullable=False)
    display_blood_group = Column(Boolean, default=True, nullable=False)
    display_allergies = Column(Boolean, default=True, nullable=False)
    display_conditions = Column(Boolean, default=True, nullable=False)
    display_medicines = Column(Boolean, default=True, nullable=False)
    display_emergency_contacts = Column(Boolean, default=True, nullable=False)
    emergency_instructions = Column(Text, default="Diabetic patient. Carry glucose tablets. Notify emergency contact immediately upon unresponsiveness.", nullable=True)
    doctor_contact_details = Column(String(200), default="Dr. Sunita Rao (Cardiologist) - +91 98450 12345", nullable=True)
    regenerated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    patient = relationship("PatientProfile")
    access_logs = relationship("QRAccessAuditLog", back_populates="qr_profile", cascade="all, delete-orphan")

    @property
    def qr_code_url(self) -> str:
        return f"/api/v1/patient/dashboard/emergency-qr/public/{self.qr_token}"


class QRAccessAuditLog(Base):
    __tablename__ = "qr_access_audit_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    qr_profile_id = Column(Integer, ForeignKey("emergency_qr_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    ip_address = Column(String(100), nullable=True)
    user_agent = Column(String(255), nullable=True)
    accessed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    qr_profile = relationship("EmergencyQRProfile", back_populates="access_logs")


# =========================================================================
# ADDITIONAL FEATURE: Digital Medical Document & AI Clinical Analysis
# =========================================================================
class DigitalMedicalDocument(Base):
    __tablename__ = "digital_medical_documents"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patient_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    document_name = Column(String(255), nullable=False)
    document_type = Column(String(100), default="lab_report", nullable=False)  # 'lab_report', 'prescription', 'ecg_strip', 'discharge_summary', 'radiology'
    file_url = Column(String(500), nullable=True)
    file_text_content = Column(Text, nullable=True)
    uploaded_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    ai_analysis_status = Column(String(50), default="completed", nullable=False)  # 'pending', 'completed', 'failed'
    ai_summary = Column(Text, nullable=True)
    ai_detected_conditions = Column(Text, nullable=True)
    ai_key_biomarkers = Column(Text, nullable=True)
    ai_clinical_suggestions = Column(Text, nullable=True)
    ai_confidence_score = Column(Float, default=0.92, nullable=False)

    patient = relationship("PatientProfile")
