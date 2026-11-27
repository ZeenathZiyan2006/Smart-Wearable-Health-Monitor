from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class NovaSuggestedAction(BaseModel):
    id: str
    label: str
    action: str
    icon: Optional[str] = None
    color: Optional[str] = None


class NovaInteractRequest(BaseModel):
    message: Optional[str] = Field("", description="Spoken or typed user prompt")
    action: Optional[str] = Field(None, description="Direct action trigger key")
    patient_id: Optional[str] = Field(None, description="Target Patient ID for caregiver/doctor review (e.g. PT-2026-000001)")
    language: Optional[str] = Field("en", description="Preferred output language: 'en', 'kn', 'hi', 'ta', 'te', 'ml'")
    mood_type: Optional[str] = Field(None, description="Optional mood identifier for wellbeing check-in")
    notes: Optional[str] = Field(None, description="Optional user notes or message text")
    context_data: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Client coordinates or situational context")


class NovaInteractResponse(BaseModel):
    text: str
    audio_text: str
    role: str
    authorized_patient_id: Optional[str] = None
    patient_name: Optional[str] = None
    status: str = "success"  # 'success', 'unauthorized', 'emergency_initiated', 'needs_patient_id', 'info'
    action_result: Optional[Dict[str, Any]] = None
    suggested_actions: List[NovaSuggestedAction] = []
    is_emergency: bool = False
    direct_call_url: Optional[str] = None
    requires_confirmation: bool = False
    confirmation_prompt: Optional[str] = None


class NovaWellbeingCreate(BaseModel):
    mood_type: str = Field(..., description="e.g. calm, happy, tired, stressed, pain, lonely, routine_fatigue")
    notes: Optional[str] = Field(None, description="Optional personal reflection notes")
    target_patient_id: Optional[str] = Field(None, description="Associated patient ID if patient self-check-in")


class NovaWellbeingItem(BaseModel):
    id: int
    role: str
    mood_type: str
    notes: Optional[str] = None
    is_caregiver_wellbeing: bool
    created_at: str


class NovaContextResponse(BaseModel):
    role: str
    user_name: str
    user_id: int
    preferred_language: str
    authorized_patients: List[Dict[str, Any]] = []
    has_active_emergency: bool = False
    capabilities: List[str] = []
