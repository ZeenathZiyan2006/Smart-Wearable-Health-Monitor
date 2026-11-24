from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.api.v1.ai import _resolve_target_patient
from app.models.user import User
from app.schemas.health_drift import (
    HealthDriftAnalysisRequest,
    HealthDriftTimelineResponse,
    MetricDriftResult,
    OverallHealthDriftSummary,
)
from app.services.health_drift_service import HealthDriftService

router = APIRouter()


# -----------------------------------------------------------------------------
# 1. Overall Health Drift Summary
# -----------------------------------------------------------------------------
@router.get("/summary", response_model=OverallHealthDriftSummary, status_code=status.HTTP_200_OK)
def get_health_drift_summary(
    patient_id: Optional[int] = Query(None, description="Patient ID (required for caregivers/admins)"),
    window_days: int = Query(7, ge=3, le=90, description="Evaluation window duration in days (default: 7)"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> OverallHealthDriftSummary:
    """
    Returns comprehensive multi-metric health drift summary, trend directions,
    EWMA moving averages, persistence scores, and multi-window (3d, 7d, 30d) comparisons.
    """
    target_patient_id = _resolve_target_patient(db, current_user, patient_id)
    return HealthDriftService.analyze_drift(
        db=db,
        patient_id=target_patient_id,
        window_days=window_days,
        persist=True
    )


# -----------------------------------------------------------------------------
# 2. Individual Metric Drift Breakdown
# -----------------------------------------------------------------------------
@router.get("/metric/{metric_name}", response_model=MetricDriftResult, status_code=status.HTTP_200_OK)
def get_metric_drift_details(
    metric_name: str = Path(..., description="Target metric: 'heart_rate', 'spo2', 'temperature', 'sleep_duration', or 'daily_steps'"),
    patient_id: Optional[int] = Query(None, description="Patient ID (required for caregivers/admins)"),
    window_days: int = Query(7, ge=3, le=90, description="Evaluation window duration in days (default: 7)"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> MetricDriftResult:
    """
    Returns in-depth statistical trajectory for a single metric, including daily aggregated data points,
    EWMA, linear regression slope, and transient vs persistent drift classification.
    """
    target_patient_id = _resolve_target_patient(db, current_user, patient_id)
    return HealthDriftService.analyze_single_metric(
        db=db,
        patient_id=target_patient_id,
        metric_name=metric_name,
        window_days=window_days
    )


# -----------------------------------------------------------------------------
# 3. Historical Drift Timeline
# -----------------------------------------------------------------------------
@router.get("/timeline", response_model=HealthDriftTimelineResponse, status_code=status.HTTP_200_OK)
def get_health_drift_timeline(
    patient_id: Optional[int] = Query(None, description="Patient ID (required for caregivers/admins)"),
    metric_name: Optional[str] = Query(None, description="Filter timeline by metric (e.g. 'heart_rate')"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of historical drift records"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> HealthDriftTimelineResponse:
    """
    Retrieves chronological audit trail of persisted health drift assessments.
    """
    target_patient_id = _resolve_target_patient(db, current_user, patient_id)
    return HealthDriftService.get_drift_timeline(
        db=db,
        patient_id=target_patient_id,
        metric_name=metric_name,
        limit=limit
    )


# -----------------------------------------------------------------------------
# 4. Configurable Time-Window Analysis (On-Demand)
# -----------------------------------------------------------------------------
@router.post("/analyze", response_model=OverallHealthDriftSummary, status_code=status.HTTP_200_OK)
def analyze_custom_health_drift(
    payload: HealthDriftAnalysisRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> OverallHealthDriftSummary:
    """
    Executes an on-demand health drift evaluation over a customized time window and metrics list.
    """
    target_patient_id = _resolve_target_patient(db, current_user, payload.patient_id)
    return HealthDriftService.analyze_drift(
        db=db,
        patient_id=target_patient_id,
        window_days=payload.window_days,
        metrics_to_analyze=payload.metrics,
        persist=payload.persist
    )
