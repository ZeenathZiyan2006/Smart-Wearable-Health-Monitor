from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class LocationLogBase(BaseModel):
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0, description="GPS latitude in decimal degrees")
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0, description="GPS longitude in decimal degrees")
    altitude: Optional[float] = Field(None, description="Altitude above sea level in meters")
    accuracy: Optional[float] = Field(None, ge=0.0, description="Horizontal accuracy radius in meters")
    speed: Optional[float] = Field(None, ge=0.0, description="Movement speed in m/s")
    is_gps_available: bool = Field(True, description="False if GPS fix was lost or unavailable when polled")
    device_battery: Optional[float] = Field(None, ge=0.0, le=100.0, description="Battery level at fix time")
    recorded_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc), description="UTC timestamp")


class LocationLogCreate(LocationLogBase):
    device_uuid: Optional[str] = Field(None, description="ESP32 hardware device identifier")
    patient_id: Optional[int] = Field(None, description="Patient ID if reported by caregiver/admin")


class LocationLogBatchCreate(BaseModel):
    device_uuid: Optional[str] = None
    patient_id: Optional[int] = None
    coordinates: List[LocationLogBase] = Field(..., min_length=1, description="List of buffered GPS breadcrumbs")


class LocationLogOut(LocationLogBase):
    id: int
    patient_id: int
    device_uuid: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LatestLocationOut(BaseModel):
    patient_id: int
    has_location: bool
    is_stale: bool = Field(..., description="True if latest GPS fix is older than 15 minutes")
    status: str = Field(..., description="'active', 'stale', 'unavailable'")
    latest_location: Optional[LocationLogOut] = None
    message: Optional[str] = None
