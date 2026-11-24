from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field


# -----------------------------------------------------------------------------
# Token Schemas
# -----------------------------------------------------------------------------
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: int
    email: str
    role: str
    full_name: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class TokenPayload(BaseModel):
    sub: Optional[str] = None
    role: Optional[str] = None
    type: Optional[str] = None
    exp: Optional[int] = None


# -----------------------------------------------------------------------------
# User Schemas
# -----------------------------------------------------------------------------
class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=255)
    phone_number: Optional[str] = Field(None, max_length=50)
    preferred_language: str = Field("en", description="Supported: en, kn, hi, ml")
    role: str = Field("patient", description="Roles: patient, caregiver, admin")


class UserCreate(UserBase):
    password: str = Field(..., min_length=6, description="Plaintext password to hash")
    
    # Optional patient-specific registration fields
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    blood_group: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    device_uuid: Optional[str] = None
    
    # Optional caregiver-specific registration fields
    relationship_type: Optional[str] = "Family"
    organization: Optional[str] = None
    notification_preference: Optional[str] = "all"


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    phone_number: Optional[str] = None
    preferred_language: Optional[str] = None
    password: Optional[str] = Field(None, min_length=6)
    is_active: Optional[bool] = None


class UserOut(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# -----------------------------------------------------------------------------
# Patient Profile Schemas
# -----------------------------------------------------------------------------
class PatientProfileBase(BaseModel):
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    blood_group: Optional[str] = None
    medical_history: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    device_uuid: Optional[str] = None
    device_status: Optional[str] = "offline"


class PatientProfileCreate(PatientProfileBase):
    user_id: int


class PatientProfileUpdate(BaseModel):
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    blood_group: Optional[str] = None
    medical_history: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    device_uuid: Optional[str] = None
    device_status: Optional[str] = None


class PatientProfileOut(PatientProfileBase):
    id: int
    user_id: int
    last_sync_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# -----------------------------------------------------------------------------
# Caregiver Profile Schemas
# -----------------------------------------------------------------------------
class CaregiverProfileBase(BaseModel):
    relationship_type: str = "Family"
    organization: Optional[str] = None
    notification_preference: str = "all"


class CaregiverProfileCreate(CaregiverProfileBase):
    user_id: int


class CaregiverProfileUpdate(BaseModel):
    relationship_type: Optional[str] = None
    organization: Optional[str] = None
    notification_preference: Optional[str] = None


class CaregiverProfileOut(CaregiverProfileBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# -----------------------------------------------------------------------------
# Patient-Caregiver Association Schemas
# -----------------------------------------------------------------------------
class PatientCaregiverAssociationCreate(BaseModel):
    patient_id: int
    caregiver_id: int
    is_primary: bool = False
    access_level: str = Field("full", description="'full', 'read_only', 'emergency_only'")
    escalation_tier: int = Field(1, ge=1, le=3, description="Escalation order: 1=first, 2=secondary, 3=tertiary")


class PatientCaregiverAssociationUpdate(BaseModel):
    is_primary: Optional[bool] = None
    access_level: Optional[str] = None
    escalation_tier: Optional[int] = Field(None, ge=1, le=3)


class PatientCaregiverAssociationOut(BaseModel):
    id: int
    patient_id: int
    caregiver_id: int
    is_primary: bool
    access_level: str
    escalation_tier: int
    created_at: datetime
    caregiver_user: Optional[UserOut] = None
    patient_user: Optional[UserOut] = None

    model_config = ConfigDict(from_attributes=True)


# -----------------------------------------------------------------------------
# Aggregated Full Profile Schema
# -----------------------------------------------------------------------------
class UserProfileOut(UserOut):
    patient_profile: Optional[PatientProfileOut] = None
    caregiver_profile: Optional[CaregiverProfileOut] = None
