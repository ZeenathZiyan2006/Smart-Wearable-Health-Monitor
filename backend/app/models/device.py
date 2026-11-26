from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    device_uuid = Column(String(100), unique=True, index=True, nullable=False)
    device_name = Column(String(100), default="PulseGuardian Wearable", nullable=False)
    model_type = Column(String(50), default="ESP32-MAX30102-MPU6050", nullable=False)
    firmware_version = Column(String(50), default="1.0.0", nullable=False)
    
    # Ownership association
    patient_id = Column(Integer, ForeignKey("patient_profiles.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Operational Status
    status = Column(String(50), default="paired", nullable=False)  # 'paired', 'connected', 'disconnected', 'unpaired'
    battery_level = Column(Float, nullable=True)
    is_simulator = Column(Boolean, default=False, nullable=False)
    config_json = Column(Text, nullable=True)  # Sampling rates, thresholds, sensor toggles
    
    last_sync_at = Column(DateTime(timezone=True), nullable=True)
    paired_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    patient = relationship("PatientProfile", foreign_keys=[patient_id])
    connection_history = relationship("DeviceConnectionHistory", back_populates="device", cascade="all, delete-orphan")


class DeviceConnectionHistory(Base):
    __tablename__ = "device_connection_history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String(50), nullable=False)  # 'paired', 'connected', 'disconnected', 'sync', 'unpaired', 'firmware_updated'
    details = Column(Text, nullable=True)
    recorded_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    device = relationship("Device", back_populates="connection_history")
