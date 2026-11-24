from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.ai import MEDICAL_DISCLAIMER


class DriftDataPoint(BaseModel):
    date: str = Field(..., description="Date of aggregated reading (YYYY-MM-DD)")
    value: Optional[float] = Field(None, description="Observed daily aggregated value")
    moving_avg: Optional[float] = Field(None, description="Moving average / EWMA value")
    baseline: float = Field(..., description="Patient baseline reference value")


class MetricDriftResult(BaseModel):
    metric_name: str = Field(..., description="Metric key ('heart_rate', 'spo2', 'temperature', 'sleep_duration', 'daily_steps')")
    display_name: str = Field(..., description="Human-readable metric label")
    unit: str = Field(..., description="Unit of measurement ('BPM', '%', '°C', 'hours', 'steps')")
    baseline_value: float = Field(..., description="Personal digital twin baseline value")
    current_value: Optional[float] = Field(None, description="Recent period aggregate (EWMA/mean)")
    drift_delta: Optional[float] = Field(None, description="Absolute difference from baseline")
    drift_percentage: Optional[float] = Field(None, description="Percentage deviation from baseline")
    trend_direction: str = Field("stable", description="'upward', 'downward', 'stable'")
    slope_per_day: Optional[float] = Field(None, description="Linear trend slope (rate of change per day)")
    persistence_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Persistence score (0.0 to 1.0)")
    is_persistent: bool = Field(False, description="True if change represents persistent shift vs temporary noise")
    classification: str = Field("stable", description="'persistent_drift', 'transient_fluctuation', 'stable'")
    significance: str = Field("stable", description="Drift significance level")
    data_sufficiency: str = Field("sufficient", description="'sufficient', 'moderate', 'insufficient'")
    recorded_days_count: int = Field(0, description="Number of days in the window with valid data")
    total_window_days: int = Field(..., description="Total days in the requested evaluation window")
    explanation: str = Field(..., description="Natural language explanation of drift findings")
    data_points: List[DriftDataPoint] = Field(default_factory=list, description="Daily time series data points")


class MultiWindowComparison(BaseModel):
    window_days: int = Field(..., description="Evaluation window duration in days")
    drift_delta: Optional[float] = None
    drift_percentage: Optional[float] = None
    trend_direction: str = "stable"
    significance: str = "stable"


class OverallHealthDriftSummary(BaseModel):
    patient_id: int
    analysis_timestamp: datetime
    window_days: int
    period_start: datetime
    period_end: datetime
    overall_drift_status: str = Field(..., description="'stable', 'mild_drift', 'moderate_drift', 'significant_drift', 'insufficient_data'")
    overall_confidence: str = Field(..., description="'high', 'medium', 'low'")
    data_completeness_percentage: float = Field(..., description="Percentage of window covered by valid telemetry")
    metrics_summary: Dict[str, MetricDriftResult] = Field(..., description="Drift analysis for each analyzed metric")
    multi_window_trends: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Comparative trends across 3-day, 7-day, and 30-day windows"
    )
    key_findings: List[str] = Field(default_factory=list, description="Primary takeaways and persistent drift warnings")
    recommendations: List[str] = Field(default_factory=list, description="Non-diagnostic observational guidance")
    medical_disclaimer: str = Field(default=MEDICAL_DISCLAIMER, description="Mandatory non-diagnostic safety disclaimer")


class HealthDriftTimelineItem(BaseModel):
    id: int
    patient_id: int
    period_start: datetime
    period_end: datetime
    drift_parameter: str
    baseline_value: float
    current_period_value: float
    drift_delta: float
    drift_percentage: float
    significance: str
    ai_recommendation: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class HealthDriftTimelineResponse(BaseModel):
    patient_id: int
    total_records: int
    records: List[HealthDriftTimelineItem]


class HealthDriftAnalysisRequest(BaseModel):
    patient_id: Optional[int] = Field(None, description="Patient ID (required for caregivers/admins)")
    window_days: int = Field(7, ge=3, le=90, description="Evaluation window in days (default: 7)")
    metrics: Optional[List[str]] = Field(None, description="Optional subset of metrics to analyze")
    persist: bool = Field(True, description="Whether to record drift analysis snapshots in the database")
