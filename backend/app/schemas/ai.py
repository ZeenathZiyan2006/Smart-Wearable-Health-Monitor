from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


MEDICAL_DISCLAIMER = (
    "PulseGuardian AI provides health tracking and anomaly detection for observational "
    "purposes only. It is not a medical diagnosis or disease prediction tool. "
    "Please consult a qualified healthcare professional."
)


class VitalReadingsInput(BaseModel):
    heart_rate: Optional[float] = Field(None, ge=20.0, le=280.0, description="Heart rate in BPM")
    spo2: Optional[float] = Field(None, ge=40.0, le=100.0, description="Blood oxygen percentage (0-100%)")
    temperature: Optional[float] = Field(None, ge=20.0, le=50.0, description="Body temperature value")
    temperature_unit: str = Field("C", description="Temperature measurement unit ('C' or 'F')")
    step_count: Optional[int] = Field(0, ge=0, description="Step count recorded")
    activity_type: Optional[str] = Field("resting", description="Activity status ('resting', 'walking', 'active', 'sleeping')")
    fall_detected: Optional[bool] = Field(False, description="Fall impact detected by MPU6050 accelerometer")
    battery_percentage: Optional[float] = Field(None, ge=0.0, le=100.0, description="Device battery percentage (0-100%)")
    recorded_at: Optional[datetime] = Field(None, description="UTC timestamp of the reading")


class AnalysisRequest(BaseModel):
    patient_id: Optional[int] = Field(None, description="Target patient ID (required for caregivers/admins if analyzing another patient)")
    vitals: Optional[VitalReadingsInput] = Field(
        None,
        description="Optional vital readings to evaluate. If omitted, patient's latest ingested reading is used."
    )


class AnomalyDetail(BaseModel):
    parameter: str = Field(..., description="Vital sign parameter ('heart_rate', 'spo2', 'temperature', 'multi_signal', 'fall_impact')")
    current_value: Optional[float] = Field(None, description="Observed value")
    baseline_value: Optional[float] = Field(None, description="Expected personal baseline value")
    deviation: Optional[float] = Field(None, description="Deviation (e.g. difference or Z-score)")
    unit: str = Field("", description="Unit of measurement")
    severity: str = Field(..., description="Severity level ('low', 'moderate', 'high', 'critical')")
    explanation: str = Field(..., description="Human-readable explanation of why this was flagged")


class DigitalTwinBaselineOut(BaseModel):
    patient_id: int
    status: str = Field("active", description="'active' or 'cold_start'")
    cold_start: bool = Field(False, description="True if insufficient data for personal baseline")
    samples_count: int = Field(0, description="Total valid readings used to construct baseline")
    min_samples_required: int = Field(20, description="Minimum readings required to exit cold start")
    baseline_resting_hr: float
    hr_min_normal: float
    hr_max_normal: float
    hr_std_dev: float
    baseline_spo2: float
    spo2_min_normal: float
    baseline_temperature: float
    temp_min_normal: float
    temp_max_normal: float
    circadian_profile: Optional[Dict[str, Any]] = Field(None, description="Hourly and day/night baseline statistics")
    last_calculated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AIAnalysisResult(BaseModel):
    patient_id: int
    analysis_timestamp: datetime
    overall_status: str = Field(..., description="'normal', 'cautionary', 'anomalous'")
    severity: str = Field(..., description="'normal', 'low', 'moderate', 'high', 'critical'")
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence score of the evaluation (0.0 to 1.0)")
    data_quality_status: str = Field("good", description="'good', 'fair', 'stale', 'incomplete', 'sensor_noise'")
    personal_baseline: Dict[str, Any] = Field(..., description="Personal digital twin baseline statistics")
    current_readings: Dict[str, Any] = Field(..., description="Evaluated readings")
    detected_anomalies: List[AnomalyDetail] = Field(default_factory=list, description="List of detected anomalies")
    isolation_forest_triggered: bool = Field(False, description="True if Scikit-learn Isolation Forest flagged multivariate anomaly")
    isolation_forest_score: Optional[float] = Field(None, description="Isolation forest decision score")
    explanation: str = Field(..., description="Comprehensive explanation of findings")
    recommendations: List[str] = Field(default_factory=list, description="Actionable non-diagnostic guidance")
    medical_disclaimer: str = Field(MEDICAL_DISCLAIMER, description="Mandatory medical safety disclaimer")


class AIHealthStatusOut(BaseModel):
    patient_id: int
    current_status: str = Field(..., description="'normal', 'cautionary', 'anomalous', 'no_data', 'stale'")
    last_reading_at: Optional[datetime] = None
    latest_vitals: Optional[Dict[str, Any]] = None
    baseline_summary: Optional[Dict[str, Any]] = None
    active_anomalies_count: int = 0
    cold_start: bool = True
    data_quality_status: str = "good"
    disclaimer: str = Field(MEDICAL_DISCLAIMER, description="Mandatory medical safety disclaimer")


class AIAnomalyItemOut(BaseModel):
    telemetry_id: int
    patient_id: int
    recorded_at: datetime
    vitals: Dict[str, Any]
    anomaly_score: float
    anomaly_reason: str
    severity: str


class AIAnomaliesResponse(BaseModel):
    patient_id: int
    total_anomalies: int
    anomalies: List[AIAnomalyItemOut]


class HealthTimelinePoint(BaseModel):
    timestamp: datetime
    heart_rate: Optional[float] = None
    spo2: Optional[float] = None
    temperature: Optional[float] = None
    step_count: Optional[int] = 0
    activity_type: Optional[str] = "resting"
    is_anomalous: bool = False
    anomaly_reason: Optional[str] = None
    baseline_resting_hr: float
    hr_lower_bound: float
    hr_upper_bound: float
    baseline_spo2: float
    spo2_lower_bound: float


class HealthTimelineResponse(BaseModel):
    patient_id: int
    time_range_hours: int
    total_points: int
    timeline: List[HealthTimelinePoint]
    cold_start: bool
