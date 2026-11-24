from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class DigitalTwinBaseline(Base):
    __tablename__ = "digital_twin_baselines"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patient_profiles.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    # Heart Rate bounds
    baseline_resting_hr = Column(Float, default=72.0, nullable=False)
    hr_min_normal = Column(Float, default=55.0, nullable=False)
    hr_max_normal = Column(Float, default=100.0, nullable=False)
    hr_std_dev = Column(Float, default=5.0, nullable=False)
    
    # Blood Oxygen (SpO2) bounds
    baseline_spo2 = Column(Float, default=98.0, nullable=False)
    spo2_min_normal = Column(Float, default=94.0, nullable=False)
    
    # Body Temperature bounds
    baseline_temperature = Column(Float, default=36.8, nullable=False)
    temp_min_normal = Column(Float, default=36.1, nullable=False)
    temp_max_normal = Column(Float, default=37.5, nullable=False)
    
    # Circadian & Statistical metadata
    circadian_profile_json = Column(Text, nullable=True)  # JSON-encoded hourly/daily baseline profiles
    samples_count = Column(Integer, default=0, nullable=False)
    last_calculated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    patient = relationship("PatientProfile", back_populates="digital_twin")


class HealthDriftRecord(Base):
    __tablename__ = "health_drift_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    patient_id = Column(Integer, ForeignKey("patient_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    drift_parameter = Column(String(50), nullable=False)  # 'resting_hr', 'spo2_trend', 'temperature_trend'
    
    baseline_value = Column(Float, nullable=False)
    current_period_value = Column(Float, nullable=False)
    drift_delta = Column(Float, nullable=False)
    drift_percentage = Column(Float, nullable=False)
    significance = Column(String(50), default="stable", nullable=False)  # 'stable', 'mild_drift', 'critical_drift'
    
    ai_recommendation = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
