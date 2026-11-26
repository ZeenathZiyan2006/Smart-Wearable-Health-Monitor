from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class DeviceBase(BaseModel):
    device_uuid: str = Field(..., min_length=3, max_length=100, description="Unique hardware MAC or UUID")
    device_name: str = Field("PulseGuardian Wearable", max_length=100)
    model_type: str = Field("ESP32-MAX30102-MPU6050", max_length=50)
    firmware_version: str = Field("1.0.0", max_length=50)


class DeviceRegister(DeviceBase):
    patient_id: Optional[int] = Field(None, description="Patient ID to associate device with")
    is_simulator: bool = Field(False, description="Whether device is a simulated test hardware")


class DeviceConfigUpdate(BaseModel):
    sampling_interval_seconds: Optional[int] = Field(None, ge=1, le=3600)
    hr_alert_threshold_high: Optional[float] = Field(None, ge=80.0, le=220.0)
    hr_alert_threshold_low: Optional[float] = Field(None, ge=30.0, le=70.0)
    spo2_alert_threshold_low: Optional[float] = Field(None, ge=70.0, le=95.0)
    fall_detection_enabled: Optional[bool] = None
    gps_tracking_interval_seconds: Optional[int] = Field(None, ge=5, le=7200)


class DeviceSimulateRequest(BaseModel):
    heart_rate: Optional[float] = Field(72.0, ge=30.0, le=240.0)
    spo2: Optional[float] = Field(98.0, ge=50.0, le=100.0)
    temperature: Optional[float] = Field(36.6, ge=30.0, le=45.0)
    step_count: Optional[int] = Field(150, ge=0)
    fall_detected: bool = Field(False)
    latitude: Optional[float] = Field(12.9716, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(77.5946, ge=-180.0, le=180.0)
    battery_level: Optional[float] = Field(95.0, ge=0.0, le=100.0)


class DeviceConnectionHistoryOut(BaseModel):
    id: int
    device_id: int
    event_type: str
    details: Optional[str] = None
    recorded_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DeviceOut(DeviceBase):
    id: int
    patient_id: Optional[int] = None
    status: str
    battery_level: Optional[float] = None
    is_simulator: bool
    config_json: Optional[str] = None
    last_sync_at: Optional[datetime] = None
    paired_at: datetime
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
