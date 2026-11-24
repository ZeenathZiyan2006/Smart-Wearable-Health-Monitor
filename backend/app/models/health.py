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
