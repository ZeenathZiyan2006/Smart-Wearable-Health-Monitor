from datetime import datetime, timezone
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class LocationLog(Base):
    __tablename__ = "location_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patient_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    device_uuid = Column(String(100), nullable=True, index=True)
    
    # Coordinate data
    latitude = Column(Float, nullable=True)     # None if GPS fix unavailable
    longitude = Column(Float, nullable=True)    # None if GPS fix unavailable
    altitude = Column(Float, nullable=True)     # Altitude in meters
    accuracy = Column(Float, nullable=True)     # GPS accuracy radius in meters
    speed = Column(Float, nullable=True)        # Speed in km/h or m/s
    
    # Hardware & GPS status
    is_gps_available = Column(Boolean, default=True, nullable=False)
    device_battery = Column(Float, nullable=True)
    
    # Timestamp (stored in UTC)
    recorded_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    patient = relationship("PatientProfile", back_populates="location_logs")
