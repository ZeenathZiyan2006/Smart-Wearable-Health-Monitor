from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class EmergencyAlertCreate(BaseModel):
    patient_id: Optional[int] = Field(None, description="Patient ID if triggered on behalf of patient")
    device_uuid: Optional[str] = Field(None, description="ESP32 hardware device identifier")
    alert_type: str = Field("manual_sos", description="'manual_sos', 'fall_detection', 'not_okay_assistance', 'vital_anomaly', 'voice_sos'")
    severity: str = Field("critical", description="'critical', 'high', 'moderate'")
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)
    location_accuracy: Optional[float] = Field(None, ge=0.0)
    voice_transcript: Optional[str] = None
    assistance_message: Optional[str] = None


class AssistanceRequestCreate(BaseModel):
    patient_id: Optional[int] = None
    device_uuid: Optional[str] = None
    message: Optional[str] = Field("Patient triggered 'I'm Not Okay' assistance request", description="Reason or symptoms")
    severity: str = Field("high", description="'high' or 'moderate'")
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)


class AlertAcknowledgeRequest(BaseModel):
    notes: Optional[str] = Field(None, description="Caregiver notes upon responding")


class AlertRejectRequest(BaseModel):
    reason: str = Field(..., min_length=3, description="Explanation for marking alert as false alarm or rejecting")


class EscalationAuditLogOut(BaseModel):
    id: int
    alert_id: int
    tier: int
    notified_caregiver_id: Optional[int] = None
    notification_channel: str
    provider: str
    recipient_address: Optional[str] = None
    status: str
    message_payload: Optional[str] = None
    error_message: Optional[str] = None
    retry_count: int
    sent_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EmergencyAlertOut(BaseModel):
    id: int
    patient_id: int
    device_uuid: Optional[str] = None
    alert_type: str
    severity: str
    status: str
    current_escalation_tier: int
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    location_accuracy: Optional[float] = None
    assistance_message: Optional[str] = None
    voice_transcript: Optional[str] = None
    detected_language: Optional[str] = None
    translated_summary: Optional[str] = None
    acknowledged_by_id: Optional[int] = None
    acknowledged_at: Optional[datetime] = None
    rejected_by_id: Optional[int] = None
    rejected_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    created_at: datetime
    audit_logs: Optional[List[EscalationAuditLogOut]] = []

    model_config = ConfigDict(from_attributes=True)
