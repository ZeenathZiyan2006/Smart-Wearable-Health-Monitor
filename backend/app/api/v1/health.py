from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import (
    get_current_active_user,
    get_db,
    get_optional_current_user,
)
from app.models.health import HealthTelemetry
from app.models.user import (
    PatientCaregiverAssociation,
    PatientProfile,
    User,
    UserRole,
)
from app.schemas.health import (
    DeviceStatusOut,
    HealthTelemetryBatchCreate,
    HealthTelemetryBatchResponse,
    HealthTelemetryCreate,
    HealthTelemetryOut,
    HealthTrendsOut,
)

router = APIRouter()

STALE_DEVICE_THRESHOLD_MINUTES = 15


def _resolve_patient_id(
    db: Session,
    current_user: Optional[User],
    requested_patient_id: Optional[int],
    device_uuid: Optional[str]
) -> int:
    """Helper to resolve the target patient profile from user session, patient_id or device_uuid."""
    # 1. Resolve from device_uuid (wearable ESP32 hardware authentication)
    if device_uuid:
        patient = db.query(PatientProfile).filter(PatientProfile.device_uuid == device_uuid).first()
        if patient:
            return patient.id
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device with UUID '{device_uuid}' is not registered to any patient."
        )

    # 2. Resolve from authenticated user
    if current_user:
        if current_user.role == UserRole.PATIENT.value:
            if not current_user.patient_profile:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Authenticated patient does not have an initialized patient profile."
                )
            return current_user.patient_profile.id

        # Caregiver / Admin sending on behalf of a patient
        if requested_patient_id:
            patient = db.query(PatientProfile).filter(PatientProfile.id == requested_patient_id).first()
            if not patient:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Patient profile {requested_patient_id} not found."
                )
            return patient.id

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Unable to resolve patient. Provide valid device_uuid, patient_id, or patient authentication."
    )


def _check_patient_read_permission(
    db: Session,
    patient_id: int,
    current_user: User
) -> None:
    """Verifies if the current user has permission to read the specified patient's health telemetry."""
    if current_user.role == UserRole.ADMIN.value:
        return

    if current_user.role == UserRole.PATIENT.value:
        if not current_user.patient_profile or current_user.patient_profile.id != patient_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You can only access your own health data."
            )
        return

    if current_user.role == UserRole.CAREGIVER.value:
        if not current_user.caregiver_profile:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Caregiver profile not found."
            )
        association = db.query(PatientCaregiverAssociation).filter(
            PatientCaregiverAssociation.patient_id == patient_id,
            PatientCaregiverAssociation.caregiver_id == current_user.caregiver_profile.id
        ).first()
        if not association:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You are not assigned to this patient."
            )


def _evaluate_acute_anomalies(
    heart_rate: Optional[float],
    spo2: Optional[float],
    temperature: Optional[float],
    fall_detected: bool,
    activity_type: str = "resting"
) -> tuple[bool, Optional[float], Optional[str]]:
    """Evaluates acute physiological redlines for real-time alerting."""
    reasons = []
    score = 0.0

    if fall_detected:
        reasons.append("Fall impact detected by MPU6050 accelerometer")
        score += 0.9

    if heart_rate is not None:
        if heart_rate > 130.0 and activity_type == "resting":
            reasons.append(f"Resting Tachycardia: High heart rate ({heart_rate:.1f} BPM)")
            score += 0.7
        elif heart_rate < 45.0:
            reasons.append(f"Bradycardia: Low heart rate ({heart_rate:.1f} BPM)")
            score += 0.7

    if spo2 is not None and spo2 < 90.0:
        reasons.append(f"Hypoxemia: Critical low SpO2 ({spo2:.1f}%)")
        score += 0.8

    if temperature is not None:
        if temperature > 38.5:
            reasons.append(f"High Fever ({temperature:.1f}°C)")
            score += 0.5
        elif temperature < 35.0:
            reasons.append(f"Hypothermia ({temperature:.1f}°C)")
            score += 0.6

    is_anomalous = len(reasons) > 0
    anomaly_reason = "; ".join(reasons) if is_anomalous else None
    anomaly_score = min(score, 1.0) if is_anomalous else 0.0

    return is_anomalous, anomaly_score, anomaly_reason


# -----------------------------------------------------------------------------
# Telemetry Ingestion Endpoints
# -----------------------------------------------------------------------------
@router.post("/telemetry", response_model=HealthTelemetryOut, status_code=status.HTTP_201_CREATED)
def ingest_telemetry(
    data: HealthTelemetryCreate,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Ingest real-time wearable health telemetry with deduplication support.
    """
    patient_id = _resolve_patient_id(db, current_user, data.patient_id, data.device_uuid)
    recorded_at = data.recorded_at or datetime.now(timezone.utc)
    if recorded_at.tzinfo is None:
        recorded_at = recorded_at.replace(tzinfo=timezone.utc)

    # Offline synchronization duplicate prevention: check if timestamp exists for this patient
    existing = db.query(HealthTelemetry).filter(
        HealthTelemetry.patient_id == patient_id,
        HealthTelemetry.recorded_at == recorded_at
    ).first()

    if existing:
        return existing

    is_anom, score, reason = _evaluate_acute_anomalies(
        heart_rate=data.heart_rate,
        spo2=data.spo2,
        temperature=data.temperature,
        fall_detected=data.fall_detected,
        activity_type=data.activity_type
    )

    now = datetime.now(timezone.utc)
    reading = HealthTelemetry(
        patient_id=patient_id,
        device_uuid=data.device_uuid,
        heart_rate=data.heart_rate,
        spo2=data.spo2,
        temperature=data.temperature,
        temperature_unit=data.temperature_unit or "C",
        step_count=data.step_count,
        activity_type=data.activity_type,
        sleep_duration_minutes=data.sleep_duration_minutes,
        fall_detected=data.fall_detected,
        accelerometer_x=data.accelerometer_x,
        accelerometer_y=data.accelerometer_y,
        accelerometer_z=data.accelerometer_z,
        battery_percentage=data.battery_percentage,
        is_anomalous=is_anom,
        anomaly_score=score,
        anomaly_reason=reason,
        recorded_at=recorded_at
    )
    db.add(reading)

    # Update patient wearable status
    patient = db.query(PatientProfile).filter(PatientProfile.id == patient_id).first()
    if patient:
        patient.device_status = "online"
        patient.last_sync_at = now
        if data.device_uuid and not patient.device_uuid:
            patient.device_uuid = data.device_uuid

    db.commit()
    db.refresh(reading)
    return reading


@router.post("/telemetry/batch", response_model=HealthTelemetryBatchResponse, status_code=status.HTTP_201_CREATED)
def ingest_batch_telemetry(
    batch: HealthTelemetryBatchCreate,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Ingest a batch of offline-buffered telemetry readings from wearable device flash storage.
    Performs duplicate prevention to ensure offline sync idempotency.
    """
    patient_id = _resolve_patient_id(db, current_user, batch.patient_id, batch.device_uuid)
    now = datetime.now(timezone.utc)

    created_readings = []
    seen_in_batch = set()
    duplicates_skipped = 0

    for item in batch.readings:
        recorded_at = item.recorded_at or now

        # Deduplication check for offline synchronization
        existing = db.query(HealthTelemetry).filter(
            HealthTelemetry.patient_id == patient_id,
            HealthTelemetry.recorded_at == recorded_at
        ).first()

        if existing or (recorded_at in seen_in_batch):
            duplicates_skipped += 1
            continue

        seen_in_batch.add(recorded_at)
        is_anom, score, reason = _evaluate_acute_anomalies(
            heart_rate=item.heart_rate,
            spo2=item.spo2,
            temperature=item.temperature,
            fall_detected=item.fall_detected,
            activity_type=item.activity_type
        )
        reading = HealthTelemetry(
            patient_id=patient_id,
            device_uuid=batch.device_uuid,
            heart_rate=item.heart_rate,
            spo2=item.spo2,
            temperature=item.temperature,
            temperature_unit=item.temperature_unit or "C",
            step_count=item.step_count,
            activity_type=item.activity_type,
            sleep_duration_minutes=item.sleep_duration_minutes,
            fall_detected=item.fall_detected,
            accelerometer_x=item.accelerometer_x,
            accelerometer_y=item.accelerometer_y,
            accelerometer_z=item.accelerometer_z,
            battery_percentage=item.battery_percentage,
            is_anomalous=is_anom,
            anomaly_score=score,
            anomaly_reason=reason,
            recorded_at=recorded_at
        )
        db.add(reading)
        created_readings.append(reading)

    patient = db.query(PatientProfile).filter(PatientProfile.id == patient_id).first()
    if patient:
        patient.device_status = "online"
        patient.last_sync_at = now

    db.commit()
    for r in created_readings:
        db.refresh(r)

    return {
        "total_received": len(batch.readings),
        "inserted": len(created_readings),
        "duplicates_skipped": duplicates_skipped,
        "readings": created_readings
    }


# -----------------------------------------------------------------------------
# Health Query Endpoints
# -----------------------------------------------------------------------------
@router.get("/latest", response_model=Optional[HealthTelemetryOut])
@router.get("/patients/{patient_id}/latest", response_model=Optional[HealthTelemetryOut])
def get_latest_telemetry(
    patient_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Retrieve the single latest recorded vital signs reading.
    """
    target_id = patient_id
    if target_id is None:
        if current_user.role == UserRole.PATIENT.value and current_user.patient_profile:
            target_id = current_user.patient_profile.id
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="patient_id parameter is required for caregivers/admins."
            )

    _check_patient_read_permission(db, target_id, current_user)
    latest = db.query(HealthTelemetry).filter(
        HealthTelemetry.patient_id == target_id
    ).order_by(HealthTelemetry.recorded_at.desc()).first()

    return latest


@router.get("/history", response_model=List[HealthTelemetryOut])
@router.get("/patients/{patient_id}/history", response_model=List[HealthTelemetryOut])
def get_telemetry_history(
    patient_id: Optional[int] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    anomalies_only: bool = False,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Query historical health telemetry data for charts and analysis.
    """
    target_id = patient_id
    if target_id is None:
        if current_user.role == UserRole.PATIENT.value and current_user.patient_profile:
            target_id = current_user.patient_profile.id
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="patient_id parameter is required for caregivers/admins."
            )

    _check_patient_read_permission(db, target_id, current_user)

    query = db.query(HealthTelemetry).filter(HealthTelemetry.patient_id == target_id)
    if start_time:
        query = query.filter(HealthTelemetry.recorded_at >= start_time)
    if end_time:
        query = query.filter(HealthTelemetry.recorded_at <= end_time)
    if anomalies_only:
        query = query.filter(HealthTelemetry.is_anomalous == True)  # noqa: E712

    return query.order_by(HealthTelemetry.recorded_at.desc()).offset(skip).limit(limit).all()


@router.get("/trends", response_model=HealthTrendsOut)
@router.get("/patients/{patient_id}/summary", response_model=Dict[str, Any])
def get_health_trends(
    patient_id: Optional[int] = None,
    hours: int = Query(24, ge=1, le=720, description="Window in hours (e.g. 24 for daily, 168 for weekly)"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Calculates aggregated health metrics, moving averages, and trajectory trend for vitals.
    """
    target_id = patient_id
    if target_id is None:
        if current_user.role == UserRole.PATIENT.value and current_user.patient_profile:
            target_id = current_user.patient_profile.id
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="patient_id parameter is required for caregivers/admins."
            )

    _check_patient_read_permission(db, target_id, current_user)

    patient = db.query(PatientProfile).filter(PatientProfile.id == target_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient {target_id} not found."
        )

    now = datetime.now(timezone.utc)
    since = now - timedelta(hours=hours)

    readings = db.query(HealthTelemetry).filter(
        HealthTelemetry.patient_id == target_id,
        HealthTelemetry.recorded_at >= since
    ).order_by(HealthTelemetry.recorded_at.asc()).all()

    total_readings = len(readings)

    if total_readings == 0:
        return {
            "patient_id": target_id,
            "time_window_hours": hours,
            "total_readings": 0,
            "heart_rate_trend": "stable",
            "avg_heart_rate": None,
            "min_heart_rate": None,
            "max_heart_rate": None,
            "avg_spo2": None,
            "min_spo2": None,
            "max_spo2": None,
            "avg_temperature": None,
            "min_temperature": None,
            "max_temperature": None,
            "total_steps": 0,
            "total_sleep_minutes": 0,
            "total_falls": 0,
            "anomaly_count": 0,
            "hourly_averages": []
        }

    # Extract metrics
    hrs = [r.heart_rate for r in readings if r.heart_rate is not None]
    spo2s = [r.spo2 for r in readings if r.spo2 is not None]
    temps = [r.temperature for r in readings if r.temperature is not None]
    steps = sum(r.step_count for r in readings if r.step_count)
    sleep = sum(r.sleep_duration_minutes for r in readings if r.sleep_duration_minutes)
    falls = sum(1 for r in readings if r.fall_detected)
    anomalies = sum(1 for r in readings if r.is_anomalous)

    # Heart rate trajectory trend: first half vs second half
    trend = "stable"
    if len(hrs) >= 4:
        mid = len(hrs) // 2
        first_half_avg = sum(hrs[:mid]) / mid
        second_half_avg = sum(hrs[mid:]) / (len(hrs) - mid)
        delta = second_half_avg - first_half_avg
        if delta > 5.0:
            trend = "increasing"
        elif delta < -5.0:
            trend = "decreasing"

    def _rnd(val: Optional[float]) -> Optional[float]:
        return round(float(val), 1) if val is not None else None

    # Group into hourly averages for charts
    hourly_dict: Dict[str, Dict[str, Any]] = {}
    for r in readings:
        hour_key = r.recorded_at.strftime("%Y-%m-%d %H:00")
        if hour_key not in hourly_dict:
            hourly_dict[hour_key] = {"hr": [], "spo2": [], "temp": []}
        if r.heart_rate is not None:
            hourly_dict[hour_key]["hr"].append(r.heart_rate)
        if r.spo2 is not None:
            hourly_dict[hour_key]["spo2"].append(r.spo2)
        if r.temperature is not None:
            hourly_dict[hour_key]["temp"].append(r.temperature)

    hourly_averages = [
        {
            "hour": k,
            "avg_hr": _rnd(sum(v["hr"]) / len(v["hr"])) if v["hr"] else None,
            "avg_spo2": _rnd(sum(v["spo2"]) / len(v["spo2"])) if v["spo2"] else None,
            "avg_temp": _rnd(sum(v["temp"]) / len(v["temp"])) if v["temp"] else None,
        }
        for k, v in sorted(hourly_dict.items())
    ]

    return {
        "patient_id": target_id,
        "time_window_hours": hours,
        "total_readings": total_readings,
        "heart_rate_trend": trend,
        "avg_heart_rate": _rnd(sum(hrs) / len(hrs)) if hrs else None,
        "min_heart_rate": _rnd(min(hrs)) if hrs else None,
        "max_heart_rate": _rnd(max(hrs)) if hrs else None,
        "avg_spo2": _rnd(sum(spo2s) / len(spo2s)) if spo2s else None,
        "min_spo2": _rnd(min(spo2s)) if spo2s else None,
        "max_spo2": _rnd(max(spo2s)) if spo2s else None,
        "avg_temperature": _rnd(sum(temps) / len(temps)) if temps else None,
        "min_temperature": _rnd(min(temps)) if temps else None,
        "max_temperature": _rnd(max(temps)) if temps else None,
        "total_steps": steps,
        "total_sleep_minutes": sleep,
        "total_falls": falls,
        "anomaly_count": anomalies,
        "hourly_averages": hourly_averages
    }


# -----------------------------------------------------------------------------
# Device Status Endpoint
# -----------------------------------------------------------------------------
@router.get("/device-status", response_model=DeviceStatusOut)
def get_device_status(
    patient_id: Optional[int] = None,
    device_uuid: Optional[str] = None,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Query real-time wearable device connectivity, battery level and stale status.
    """
    target_id: Optional[int] = None

    if device_uuid:
        patient = db.query(PatientProfile).filter(PatientProfile.device_uuid == device_uuid).first()
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Device '{device_uuid}' not registered."
            )
        target_id = patient.id
    elif patient_id:
        target_id = patient_id
    elif current_user and current_user.role == UserRole.PATIENT.value and current_user.patient_profile:
        target_id = current_user.patient_profile.id
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide patient_id or device_uuid."
        )

    if current_user:
        _check_patient_read_permission(db, target_id, current_user)

    patient = db.query(PatientProfile).filter(PatientProfile.id == target_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient {target_id} not found."
        )

    latest_reading = db.query(HealthTelemetry).filter(
        HealthTelemetry.patient_id == target_id
    ).order_by(HealthTelemetry.recorded_at.desc()).first()

    now = datetime.now(timezone.utc)
    is_stale = True
    battery = None
    last_rec = None

    if latest_reading:
        battery = latest_reading.battery_percentage
        last_rec = latest_reading.recorded_at
        if latest_reading.recorded_at:
            rec_at = latest_reading.recorded_at
            if rec_at.tzinfo is None:
                rec_at = rec_at.replace(tzinfo=timezone.utc)
            is_stale = (now - rec_at) > timedelta(minutes=STALE_DEVICE_THRESHOLD_MINUTES)

    is_online = (not is_stale) and (patient.device_status == "online")

    effective_status = "online" if is_online else ("stale" if is_stale and patient.last_sync_at else "offline")

    return {
        "patient_id": target_id,
        "device_uuid": patient.device_uuid,
        "device_status": effective_status,
        "battery_percentage": battery,
        "is_online": is_online,
        "is_stale": is_stale,
        "last_sync_at": patient.last_sync_at,
        "last_recorded_at": last_rec,
        "sensor_status": {
            "max30102_heart_rate_spo2": "active" if is_online else "inactive",
            "mpu6050_accelerometer": "active" if is_online else "inactive",
            "gps_neo6m": "active" if is_online else "inactive"
        }
    }
