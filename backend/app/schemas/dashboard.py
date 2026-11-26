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
