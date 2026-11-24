from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class HealthTelemetryBase(BaseModel):
    heart_rate: Optional[float] = Field(None, ge=30.0, le=260.0, description="Heart rate in BPM")
    spo2: Optional[float] = Field(None, ge=50.0, le=100.0, description="Blood oxygen percentage (0-100%)")
    temperature: Optional[float] = Field(None, ge=20.0, le=50.0, description="Body temperature value")
    temperature_unit: str = Field("C", description="Temperature measurement unit ('C' or 'F')")
    step_count: int = Field(0, ge=0, description="Step count recorded")
    activity_type: str = Field("resting", description="Activity status ('resting', 'walking', 'active', 'sleeping')")
    sleep_duration_minutes: Optional[int] = Field(None, ge=0, description="Recorded sleep duration in minutes")
    fall_detected: bool = Field(False, description="Fall impact detected by MPU6050 accelerometer")
    accelerometer_x: Optional[float] = Field(None, description="MPU6050 X-axis acceleration")
    accelerometer_y: Optional[float] = Field(None, description="MPU6050 Y-axis acceleration")
    accelerometer_z: Optional[float] = Field(None, description="MPU6050 Z-axis acceleration")
    battery_percentage: Optional[float] = Field(None, ge=0.0, le=100.0, description="Wearable battery percentage (0-100%)")
    recorded_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc), description="UTC timestamp of reading")


class HealthTelemetryCreate(HealthTelemetryBase):
    device_uuid: Optional[str] = Field(None, description="ESP32 hardware device identifier")
    patient_id: Optional[int] = Field(None, description="Patient ID if ingested by caregiver/admin")


class HealthTelemetryBatchCreate(BaseModel):
    device_uuid: Optional[str] = None
    patient_id: Optional[int] = None
    readings: List[HealthTelemetryBase] = Field(..., min_length=1, description="List of buffered telemetry readings")


class HealthTelemetryOut(HealthTelemetryBase):
    id: int
    patient_id: int
    device_uuid: Optional[str] = None
    is_anomalous: bool
    anomaly_score: Optional[float] = None
    anomaly_reason: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class HealthTelemetryBatchResponse(BaseModel):
    total_received: int
    inserted: int
    duplicates_skipped: int
    readings: List[HealthTelemetryOut]


class HealthTrendsOut(BaseModel):
    patient_id: int
    time_window_hours: int
    total_readings: int
    heart_rate_trend: str = Field("stable", description="'stable', 'increasing', 'decreasing'")
    avg_heart_rate: Optional[float] = None
    min_heart_rate: Optional[float] = None
    max_heart_rate: Optional[float] = None
    avg_spo2: Optional[float] = None
    min_spo2: Optional[float] = None
    max_spo2: Optional[float] = None
    avg_temperature: Optional[float] = None
    min_temperature: Optional[float] = None
    max_temperature: Optional[float] = None
    total_steps: int = 0
    total_sleep_minutes: Optional[int] = None
    total_falls: int = 0
    anomaly_count: int = 0
    hourly_averages: List[Dict[str, Any]] = []


class DeviceStatusOut(BaseModel):
    patient_id: int
    device_uuid: Optional[str] = None
    device_status: str = Field(..., description="'online', 'offline', 'syncing', 'stale'")
    battery_percentage: Optional[float] = None
    is_online: bool
    is_stale: bool = Field(..., description="True if no reading has been received for >15 minutes")
    last_sync_at: Optional[datetime] = None
    last_recorded_at: Optional[datetime] = None
    sensor_status: Dict[str, str] = Field(
        default_factory=lambda: {"max30102": "active", "mpu6050": "active", "gps": "active"}
    )
