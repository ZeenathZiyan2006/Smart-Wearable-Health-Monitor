"""
Pydantic Schemas for Patient Dashboard Modules:
Medicines, Intake Logs, Reminders, Appointments, Medical History, Allergies, Hydration
"""
from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


# Module 4: Medicine Management Schemas
class PatientMedicineCreate(BaseModel):
    medicine_name: str = Field(..., min_length=1, max_length=200)
    dosage: str = Field(..., min_length=1, max_length=100)
    frequency: str = Field(..., min_length=1, max_length=100)
    scheduled_times: str = Field(default="08:00,20:00", description="Comma-separated times e.g. 08:00,20:00")
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    total_quantity: int = Field(default=30, ge=1)
    remaining_quantity: int = Field(default=30, ge=0)
    medicine_status: str = Field(default="active")
    notes: Optional[str] = None


class PatientMedicineUpdate(BaseModel):
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    scheduled_times: Optional[str] = None
    end_date: Optional[datetime] = None
    remaining_quantity: Optional[int] = None
    medicine_status: Optional[str] = None
    notes: Optional[str] = None


class PatientMedicineOut(BaseModel):
    id: int
    patient_id: int
    medicine_name: str
    dosage: str
    frequency: str
    scheduled_times: str
    start_date: datetime
    end_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    total_quantity: int
    remaining_quantity: int
    medicine_status: str
    consumed_quantity: int = 0
    is_low_stock: bool = False
    is_expired: bool = False
    notes: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MedicineActionRequest(BaseModel):
    status: str = Field(..., description="'taken', 'skipped', 'missed'")
    scheduled_time: Optional[datetime] = None
    notes: Optional[str] = None


class MedicineIntakeLogOut(BaseModel):
    id: int
    medicine_id: int
    patient_id: int
    scheduled_time: datetime
    action_time: datetime
    status: str
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# Module 5: Reminders & Alarm Schemas
class PatientReminderCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    reminder_type: str = Field(default="medicine", description="'medicine', 'sleep', 'hydration', 'appointment'")
    reminder_time: str = Field(..., description="e.g. '08:00'")
    is_enabled: bool = True
    recurring_days: str = Field(default="Daily")
    alarm_tone: str = Field(default="chime_gentle")
    volume: int = Field(default=80, ge=0, le=100)
    vibration_enabled: bool = True
    snooze_interval_minutes: int = Field(default=10, ge=1)


class PatientReminderUpdate(BaseModel):
    title: Optional[str] = None
    reminder_time: Optional[str] = None
    is_enabled: Optional[bool] = None
    recurring_days: Optional[str] = None
    alarm_tone: Optional[str] = None
    volume: Optional[int] = None
    vibration_enabled: Optional[bool] = None
    snooze_interval_minutes: Optional[int] = None


class PatientReminderOut(BaseModel):
    id: int
    patient_id: int
    title: str
    reminder_type: str
    reminder_time: str
    is_enabled: bool
    recurring_days: str
    alarm_tone: str
    volume: int
    vibration_enabled: bool
    snooze_interval_minutes: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Module 7: Doctor Appointments Schemas
class DoctorAppointmentCreate(BaseModel):
    doctor_name: str = Field(..., min_length=1, max_length=150)
    specialization: str = Field(default="Cardiologist")
    hospital_name: str = Field(default="PulseGuardian Heart Center")
    phone_number: Optional[str] = None
    appointment_date: datetime
    reason: Optional[str] = None
    notes: Optional[str] = None


class DoctorAppointmentUpdate(BaseModel):
    appointment_date: Optional[datetime] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class DoctorAppointmentOut(BaseModel):
    id: int
    patient_id: int
    doctor_name: str
    specialization: str
    hospital_name: str
    phone_number: Optional[str] = None
    appointment_date: datetime
    status: str
    reason: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Module 2: Medical Conditions & Allergies Schemas
class MedicalConditionCreate(BaseModel):
    condition_name: str = Field(..., min_length=1, max_length=200)
    diagnosed_date: Optional[datetime] = None
    severity: str = Field(default="moderate")
    status: str = Field(default="active")
    notes: Optional[str] = None


class MedicalConditionOut(BaseModel):
    id: int
    patient_id: int
    condition_name: str
    diagnosed_date: Optional[datetime] = None
    severity: str
    status: str
    notes: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AllergyCreate(BaseModel):
    allergen: str = Field(..., min_length=1, max_length=200)
    reaction: Optional[str] = None
    severity: str = Field(default="moderate")


class AllergyOut(BaseModel):
    id: int
    patient_id: int
    allergen: str
    reaction: Optional[str] = None
    severity: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Hydration Log Schema
class HydrationLogCreate(BaseModel):
    intake_ml: int = Field(default=250, ge=50, le=2000)


class HydrationSummaryOut(BaseModel):
    total_intake_ml: int
    target_intake_ml: int = 2500
    percentage: float
    logs_count: int


# =========================================================================
# MODULE 1: AI Early Warning Prediction Schemas
# =========================================================================
class EarlyWarningPredictionCreate(BaseModel):
    risk_level: str = Field(default="normal")  # 'normal', 'low', 'moderate', 'high'
    parameter_changed: str
    previous_value: str
    current_value: str
    observed_pattern: str
    recommendation: str
    alert_triggered: bool = False


class EarlyWarningPredictionOut(BaseModel):
    id: int
    patient_id: int
    risk_level: str
    parameter_changed: str
    previous_value: str
    current_value: str
    observed_pattern: str
    recommendation: str
    alert_triggered: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EarlyWarningDashboardSummary(BaseModel):
    overall_health_status: str
    overall_risk_level: str
    active_abnormal_count: int
    predictions: List[EarlyWarningPredictionOut]
    trend_history_daily: List[dict]
    trend_history_weekly: List[dict]
    trend_history_monthly: List[dict]
    ai_health_explanation: str
    analyzed_at: datetime


# =========================================================================
# MODULE 2: Fall Detection Schemas
# =========================================================================
class FallEventCreate(BaseModel):
    device_uuid: Optional[str] = None
    confidence_score: float = Field(default=0.88, ge=0.0, le=1.0)
    impact_g: float = Field(default=3.2)
    orientation_change_deg: float = Field(default=75.0)
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class FallConfirmRequest(BaseModel):
    action: str = Field(..., description="'safe', 'help', 'family'")  # 'safe', 'help', 'family'
    notes: Optional[str] = None


class FallEventOut(BaseModel):
    id: int
    patient_id: int
    device_uuid: Optional[str] = None
    status: str
    confidence_score: float
    impact_g: float
    orientation_change_deg: float
    confirmation_timeout_sec: int
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    patient_response: Optional[str] = None
    escalated_at: Optional[datetime] = None
    recorded_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =========================================================================
# MODULE 3: Abnormal Inactivity Schemas
# =========================================================================
class InactivityEventCreate(BaseModel):
    device_uuid: Optional[str] = None
    inactivity_duration_minutes: int = Field(..., ge=1)
    threshold_minutes: int = Field(default=120)
    during_sleep_schedule: bool = False
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class InactivityConfirmRequest(BaseModel):
    action: str = Field(..., description="'safe', 'help'")


class InactivityEventOut(BaseModel):
    id: int
    patient_id: int
    device_uuid: Optional[str] = None
    inactivity_duration_minutes: int
    threshold_minutes: int
    during_sleep_schedule: bool
    status: str
    patient_response: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    recorded_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =========================================================================
# MODULE 4: Voice Assistant Settings & Voice Interaction Schemas
# =========================================================================
class VoiceAssistantSettingUpdate(BaseModel):
    is_enabled: Optional[bool] = None
    preferred_language: Optional[str] = None  # 'en', 'kn', 'hi'
    voice_id: Optional[str] = None
    speech_speed: Optional[float] = Field(None, ge=0.5, le=2.0)
    volume: Optional[float] = Field(None, ge=0.0, le=1.0)


class VoiceAssistantSettingOut(BaseModel):
    id: int
    patient_id: int
    is_enabled: bool
    preferred_language: str
    voice_id: str
    speech_speed: float
    volume: float
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class VoiceQueryRequest(BaseModel):
    query_text: str = Field(..., min_length=1)
    language: str = Field(default="en")  # 'en', 'kn', 'hi'


class VoiceQueryResponse(BaseModel):
    response_text: str
    intent: str
    data_payload: Optional[dict] = None
    audio_tts_prompt: str


# =========================================================================
# MODULE 5: Nearest Hospital & Emergency Facility Schemas
# =========================================================================
class HospitalFacilityOut(BaseModel):
    name: str
    address: str
    distance_km: float
    phone: str
    emergency_available_24_7: bool
    google_maps_navigate_url: str


class HospitalEmergencySettingsUpdate(BaseModel):
    is_enabled: Optional[bool] = None
    preferred_hospital_name: Optional[str] = None
    preferred_hospital_phone: Optional[str] = None
    fixed_family_doctor_name: Optional[str] = None
    fixed_family_doctor_phone: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    location_sharing_permitted: Optional[bool] = None


class HospitalEmergencySettingsOut(BaseModel):
    id: int
    patient_id: int
    is_enabled: bool
    preferred_hospital_name: str
    preferred_hospital_phone: str
    fixed_family_doctor_name: str
    fixed_family_doctor_phone: str
    emergency_contact_phone: str
    location_sharing_permitted: bool
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# =========================================================================
# MODULE 6: Medicine Adherence Intelligence Schemas
# =========================================================================
class MedicineStockAlertOut(BaseModel):
    medicine_id: int
    medicine_name: str
    total_quantity: int
    remaining_quantity: int
    estimated_days_left: int
    is_low_stock: bool
    is_expired: bool
    expiry_date: Optional[datetime] = None


class AdherenceReportOut(BaseModel):
    period: str  # 'weekly' or 'monthly'
    total_scheduled_doses: int
    doses_taken: int
    doses_missed: int
    doses_skipped: int
    adherence_percentage: float
    adherence_status: str  # 'Excellent', 'Good', 'Needs Attention'
    medicines_requiring_refill: List[MedicineStockAlertOut]
    explanation: str


# =========================================================================
# MODULE 7: Emergency Medical QR Profile Schemas
# =========================================================================
class EmergencyQRProfileUpdate(BaseModel):
    is_active: Optional[bool] = None
    blood_group: Optional[str] = None
    display_blood_group: Optional[bool] = None
    display_allergies: Optional[bool] = None
    display_conditions: Optional[bool] = None
    display_medicines: Optional[bool] = None
    display_emergency_contacts: Optional[bool] = None
    emergency_instructions: Optional[str] = None
    doctor_contact_details: Optional[str] = None


class EmergencyQRProfileOut(BaseModel):
    id: int
    patient_id: int
    qr_token: str
    qr_code_url: str
    is_active: bool
    blood_group: str
    display_blood_group: bool
    display_allergies: bool
    display_conditions: bool
    display_medicines: bool
    display_emergency_contacts: bool
    emergency_instructions: Optional[str] = None
    doctor_contact_details: Optional[str] = None
    regenerated_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EmergencyQRPublicView(BaseModel):
    patient_name: str
    patient_id_readable: str
    blood_group: Optional[str] = None
    allergies: List[str] = []
    medical_conditions: List[str] = []
    active_medicines: List[str] = []
    emergency_contacts: List[dict] = []
    emergency_instructions: Optional[str] = None
    doctor_contact: Optional[str] = None
    uploaded_documents: List[dict] = []
    is_verified: bool = True
    notice: str = "Confidential Emergency Profile. Authorized for emergency medical personnel and first responders."


# =========================================================================
# ADDITIONAL FEATURE: Digital Medical Document & AI Clinical Analysis Schemas
# =========================================================================
class DigitalDocumentUpload(BaseModel):
    document_name: str = Field(..., min_length=1, max_length=255)
    document_type: str = Field(default="lab_report")  # 'lab_report', 'prescription', 'ecg_strip', 'discharge_summary', 'radiology'
    file_text_content: Optional[str] = Field(None, description="Extracted OCR text or clinical summary")


class DigitalDocumentOut(BaseModel):
    id: int
    patient_id: int
    document_name: str
    document_type: str
    file_url: Optional[str] = None
    uploaded_at: datetime
    ai_analysis_status: str
    ai_summary: Optional[str] = None
    ai_detected_conditions: Optional[str] = None
    ai_key_biomarkers: Optional[str] = None
    ai_clinical_suggestions: Optional[str] = None
    ai_confidence_score: float

    model_config = ConfigDict(from_attributes=True)
