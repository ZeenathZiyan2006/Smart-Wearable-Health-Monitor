from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.models.health import HealthTelemetry
from app.models.user import (
    PatientCaregiverAssociation,
    PatientProfile,
    User,
    UserRole,
)
from app.schemas.ai import (
    AIAnalysisResult,
    AIAnomaliesResponse,
    AIAnomalyItemOut,
    AIHealthStatusOut,
    AnalysisRequest,
    DigitalTwinBaselineOut,
    HealthTimelinePoint,
    HealthTimelineResponse,
    MEDICAL_DISCLAIMER,
)
from app.services.anomaly_detector import AnomalyDetectorService
from app.services.digital_twin_service import DigitalTwinService

router = APIRouter()


def _resolve_target_patient(
    db: Session,
    current_user: User,
    requested_patient_id: Optional[int]
) -> int:
    """Resolves and enforces RBAC access permissions for patient data access."""
    if current_user.role == UserRole.PATIENT.value:
        if not current_user.patient_profile:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Patient profile not found for authenticated user."
            )
        if requested_patient_id and requested_patient_id != current_user.patient_profile.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You can only access your own health data."
            )
        return current_user.patient_profile.id

    if current_user.role in (UserRole.CAREGIVER.value, UserRole.ADMIN.value):
        if not requested_patient_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="patient_id parameter is required for caregiver or admin requests."
            )
        patient = db.query(PatientProfile).filter(PatientProfile.id == requested_patient_id).first()
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Patient profile {requested_patient_id} not found."
            )
        if current_user.role == UserRole.CAREGIVER.value:
            if not current_user.caregiver_profile:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Caregiver profile not found."
                )
            association = db.query(PatientCaregiverAssociation).filter(
                PatientCaregiverAssociation.patient_id == requested_patient_id,
                PatientCaregiverAssociation.caregiver_id == current_user.caregiver_profile.id
            ).first()
            if not association:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: You are not assigned to this patient."
                )
        return patient.id

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Operation not permitted."
    )


# -----------------------------------------------------------------------------
# 1. On-Demand / Telemetry Anomaly Analysis
# -----------------------------------------------------------------------------
@router.post("/analyze", response_model=AIAnalysisResult, status_code=status.HTTP_200_OK)
def analyze_health_telemetry(
    payload: AnalysisRequest = AnalysisRequest(),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> AIAnalysisResult:
    """
    Evaluates vital readings using personal Digital Twin baselines, statistical Z-scores,
    circadian context, multi-signal patterns, and Scikit-learn Isolation Forest.
    """
    target_patient_id = _resolve_target_patient(db, current_user, payload.patient_id)
    return AnomalyDetectorService.analyze_vitals(
        db=db,
        patient_id=target_patient_id,
        vitals_input=payload.vitals
    )


# -----------------------------------------------------------------------------
# 2. Real-Time Health Status Overview
# -----------------------------------------------------------------------------
@router.get("/health-status", response_model=AIHealthStatusOut, status_code=status.HTTP_200_OK)
def get_ai_health_status(
    patient_id: Optional[int] = Query(None, description="Patient ID (required for caregivers)"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> AIHealthStatusOut:
    """
    Retrieves the real-time AI monitoring status summary, active anomalies count,
    data quality, and digital twin baseline comparison.
    """
    target_patient_id = _resolve_target_patient(db, current_user, patient_id)

    # Latest reading
    latest = db.query(HealthTelemetry).filter(
        HealthTelemetry.patient_id == target_patient_id
    ).order_by(HealthTelemetry.recorded_at.desc()).first()

    baseline, is_cold_start = DigitalTwinService.get_or_calculate_baseline(db, target_patient_id)

    if not latest:
        return AIHealthStatusOut(
            patient_id=target_patient_id,
            current_status="no_data",
            last_reading_at=None,
            latest_vitals=None,
            baseline_summary={
                "resting_hr": baseline.baseline_resting_hr,
                "spo2": baseline.baseline_spo2,
                "temperature": baseline.baseline_temperature,
                "cold_start": is_cold_start,
            },
            active_anomalies_count=0,
            cold_start=is_cold_start,
            data_quality_status="incomplete",
            disclaimer=MEDICAL_DISCLAIMER
        )

    # Active anomalies in last 24 hours
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    active_anomalies_count = db.query(HealthTelemetry).filter(
        HealthTelemetry.patient_id == target_patient_id,
        HealthTelemetry.is_anomalous == True,  # noqa: E712
        HealthTelemetry.recorded_at >= cutoff
    ).count()

    # Determine real-time status
    rec_time = latest.recorded_at if latest.recorded_at.tzinfo else latest.recorded_at.replace(tzinfo=timezone.utc)
    is_stale = (datetime.now(timezone.utc) - rec_time).total_seconds() > (15 * 60)

    if is_stale:
        data_quality = "stale"
        current_status = "stale"
    elif latest.is_anomalous:
        data_quality = "good"
        current_status = "anomalous"
    else:
        data_quality = "good"
        current_status = "cautionary" if active_anomalies_count > 0 else "normal"

    return AIHealthStatusOut(
        patient_id=target_patient_id,
        current_status=current_status,
        last_reading_at=latest.recorded_at,
        latest_vitals={
            "heart_rate": latest.heart_rate,
            "spo2": latest.spo2,
            "temperature": latest.temperature,
            "temperature_unit": latest.temperature_unit,
            "step_count": latest.step_count,
            "activity_type": latest.activity_type,
            "fall_detected": latest.fall_detected,
            "is_anomalous": latest.is_anomalous,
            "anomaly_reason": latest.anomaly_reason,
        },
        baseline_summary={
            "resting_hr": baseline.baseline_resting_hr,
            "hr_min_normal": baseline.hr_min_normal,
            "hr_max_normal": baseline.hr_max_normal,
            "spo2": baseline.baseline_spo2,
            "spo2_min_normal": baseline.spo2_min_normal,
            "temperature": baseline.baseline_temperature,
            "cold_start": is_cold_start,
            "samples_count": baseline.samples_count,
        },
        active_anomalies_count=active_anomalies_count,
        cold_start=is_cold_start,
        data_quality_status=data_quality,
        disclaimer=MEDICAL_DISCLAIMER
    )


# -----------------------------------------------------------------------------
# 3. Anomaly History
# -----------------------------------------------------------------------------
@router.get("/anomalies", response_model=AIAnomaliesResponse, status_code=status.HTTP_200_OK)
def get_ai_anomalies(
    patient_id: Optional[int] = Query(None, description="Patient ID (required for caregivers)"),
    limit: int = Query(20, ge=1, le=100, description="Max anomalies to return"),
    severity: Optional[str] = Query(None, description="Filter by severity ('critical', 'high', 'moderate', 'low')"),
    start_time: Optional[datetime] = Query(None, description="Filter readings after UTC datetime"),
    end_time: Optional[datetime] = Query(None, description="Filter readings before UTC datetime"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> AIAnomaliesResponse:
    """
    Returns historical anomalies flagged for the patient with explanation, severity,
    and vital signs context.
    """
    target_patient_id = _resolve_target_patient(db, current_user, patient_id)

    query = db.query(HealthTelemetry).filter(
        HealthTelemetry.patient_id == target_patient_id,
        HealthTelemetry.is_anomalous == True  # noqa: E712
    )

    if start_time:
        query = query.filter(HealthTelemetry.recorded_at >= start_time)
    if end_time:
        query = query.filter(HealthTelemetry.recorded_at <= end_time)

    records = query.order_by(desc(HealthTelemetry.recorded_at)).limit(limit * 2).all()

    anomalies: List[AIAnomalyItemOut] = []
    for r in records:
        score = r.anomaly_score or 0.0
        if r.fall_detected or score >= 0.85:
            rec_sev = "critical"
        elif score >= 0.65:
            rec_sev = "high"
        elif score >= 0.40:
            rec_sev = "moderate"
        else:
            rec_sev = "low"

        if severity and rec_sev != severity.lower():
            continue

        anomalies.append(AIAnomalyItemOut(
            telemetry_id=r.id,
            patient_id=r.patient_id,
            recorded_at=r.recorded_at,
            vitals={
                "heart_rate": r.heart_rate,
                "spo2": r.spo2,
                "temperature": r.temperature,
                "temperature_unit": r.temperature_unit,
                "step_count": r.step_count,
                "activity_type": r.activity_type,
                "fall_detected": r.fall_detected,
            },
            anomaly_score=round(score, 3),
            anomaly_reason=r.anomaly_reason or "Physiological anomaly detected",
            severity=rec_sev
        ))

        if len(anomalies) >= limit:
            break

    return AIAnomaliesResponse(
        patient_id=target_patient_id,
        total_anomalies=len(anomalies),
        anomalies=anomalies
    )


# -----------------------------------------------------------------------------
# 4. Digital Twin Full Model
# -----------------------------------------------------------------------------
@router.get("/digital-twin", response_model=DigitalTwinBaselineOut, status_code=status.HTTP_200_OK)
def get_digital_twin_model(
    patient_id: Optional[int] = Query(None, description="Patient ID (required for caregivers)"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> DigitalTwinBaselineOut:
    """
    Returns the comprehensive Personal Health Digital Twin baseline including
    circadian day/night patterns and hourly resting profiles.
    """
    target_patient_id = _resolve_target_patient(db, current_user, patient_id)
    baseline, is_cold_start = DigitalTwinService.get_or_calculate_baseline(db, target_patient_id)
    circadian = DigitalTwinService.get_circadian_profile(baseline)

    return DigitalTwinBaselineOut(
        patient_id=baseline.patient_id,
        status="cold_start" if is_cold_start else "active",
        cold_start=is_cold_start,
        samples_count=baseline.samples_count,
        min_samples_required=20,
        baseline_resting_hr=baseline.baseline_resting_hr,
        hr_min_normal=baseline.hr_min_normal,
        hr_max_normal=baseline.hr_max_normal,
        hr_std_dev=baseline.hr_std_dev,
        baseline_spo2=baseline.baseline_spo2,
        spo2_min_normal=baseline.spo2_min_normal,
        baseline_temperature=baseline.baseline_temperature,
        temp_min_normal=baseline.temp_min_normal,
        temp_max_normal=baseline.temp_max_normal,
        circadian_profile=circadian,
        last_calculated_at=baseline.last_calculated_at
    )


# -----------------------------------------------------------------------------
# 5. Digital Twin Baseline & Recalculation
# -----------------------------------------------------------------------------
@router.get("/digital-twin/baseline", response_model=DigitalTwinBaselineOut, status_code=status.HTTP_200_OK)
def get_digital_twin_baseline(
    patient_id: Optional[int] = Query(None, description="Patient ID (required for caregivers)"),
    recalculate: bool = Query(False, description="Force re-learning baseline from telemetry"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> DigitalTwinBaselineOut:
    """
    Retrieves or recalculates the personal baseline parameters.
    """
    target_patient_id = _resolve_target_patient(db, current_user, patient_id)
    baseline, is_cold_start = DigitalTwinService.get_or_calculate_baseline(
        db, target_patient_id, force_recalculate=recalculate
    )
    circadian = DigitalTwinService.get_circadian_profile(baseline)

    return DigitalTwinBaselineOut(
        patient_id=baseline.patient_id,
        status="cold_start" if is_cold_start else "active",
        cold_start=is_cold_start,
        samples_count=baseline.samples_count,
        min_samples_required=20,
        baseline_resting_hr=baseline.baseline_resting_hr,
        hr_min_normal=baseline.hr_min_normal,
        hr_max_normal=baseline.hr_max_normal,
        hr_std_dev=baseline.hr_std_dev,
        baseline_spo2=baseline.baseline_spo2,
        spo2_min_normal=baseline.spo2_min_normal,
        baseline_temperature=baseline.baseline_temperature,
        temp_min_normal=baseline.temp_min_normal,
        temp_max_normal=baseline.temp_max_normal,
        circadian_profile=circadian,
        last_calculated_at=baseline.last_calculated_at
    )


# -----------------------------------------------------------------------------
# 6. Health Timeline (Readings vs Personal Envelope)
# -----------------------------------------------------------------------------
@router.get("/health-timeline", response_model=HealthTimelineResponse, status_code=status.HTTP_200_OK)
def get_health_timeline(
    patient_id: Optional[int] = Query(None, description="Patient ID (required for caregivers)"),
    hours: int = Query(24, ge=1, le=168, description="Time window in hours"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> HealthTimelineResponse:
    """
    Returns time-series telemetry mapped against patient-specific baseline envelopes,
    with flagged anomaly markers suitable for UI graphs.
    """
    target_patient_id = _resolve_target_patient(db, current_user, patient_id)
    baseline, is_cold_start = DigitalTwinService.get_or_calculate_baseline(db, target_patient_id)

    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    records = db.query(HealthTelemetry).filter(
        HealthTelemetry.patient_id == target_patient_id,
        HealthTelemetry.recorded_at >= cutoff
    ).order_by(HealthTelemetry.recorded_at.asc()).all()

    timeline_points = [
        HealthTimelinePoint(
            timestamp=r.recorded_at,
            heart_rate=r.heart_rate,
            spo2=r.spo2,
            temperature=r.temperature,
            step_count=r.step_count or 0,
            activity_type=r.activity_type or "resting",
            is_anomalous=r.is_anomalous,
            anomaly_reason=r.anomaly_reason,
            baseline_resting_hr=baseline.baseline_resting_hr,
            hr_lower_bound=baseline.hr_min_normal,
            hr_upper_bound=baseline.hr_max_normal,
            baseline_spo2=baseline.baseline_spo2,
            spo2_lower_bound=baseline.spo2_min_normal,
        )
        for r in records
    ]

    return HealthTimelineResponse(
        patient_id=target_patient_id,
        time_range_hours=hours,
        total_points=len(timeline_points),
        timeline=timeline_points,
        cold_start=is_cold_start
    )
