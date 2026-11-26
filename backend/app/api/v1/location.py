from datetime import datetime, timedelta, timezone
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import (
    get_current_active_user,
    get_db,
    get_optional_current_user,
)
from app.api.v1.health import _check_patient_read_permission, _resolve_patient_id
from app.models.location import LocationLog
from app.models.user import PatientProfile, User
from app.schemas.location import (
    LatestLocationOut,
    LocationLogBatchCreate,
    LocationLogCreate,
    LocationLogOut,
)

router = APIRouter()

STALE_GPS_THRESHOLD_MINUTES = 15


@router.post("/track", response_model=LocationLogOut, status_code=status.HTTP_201_CREATED)
def record_location(
    data: LocationLogCreate,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Record real-time GPS coordinate from wearable device or mobile companion app.
    Safely handles GPS unavailable flags without inventing false coordinates.
    """
    patient_id = _resolve_patient_id(db, current_user, data.patient_id, data.device_uuid)
    now = datetime.now(timezone.utc)
    recorded_at = data.recorded_at or now
    if recorded_at.tzinfo is None:
        recorded_at = recorded_at.replace(tzinfo=timezone.utc)

    # Validate coordinates when GPS is claimed to be available
    if data.is_gps_available:
        if data.latitude is None or data.longitude is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Latitude and longitude must be provided when is_gps_available is True."
            )
    else:
        # GPS is reported lost/unavailable - do not invent coordinates
        data.latitude = None
        data.longitude = None

    location_entry = LocationLog(
        patient_id=patient_id,
        device_uuid=data.device_uuid,
        latitude=data.latitude,
        longitude=data.longitude,
        altitude=data.altitude,
        accuracy=data.accuracy,
        speed=data.speed,
        is_gps_available=data.is_gps_available,
        device_battery=data.device_battery,
        recorded_at=recorded_at
    )
    db.add(location_entry)
    db.commit()
    db.refresh(location_entry)
    return location_entry


@router.post("/track/batch", response_model=List[LocationLogOut], status_code=status.HTTP_201_CREATED)
def record_batch_location(
    batch: LocationLogBatchCreate,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Upload a batch of offline-buffered GPS coordinates recorded during disconnected states.
    """
    patient_id = _resolve_patient_id(db, current_user, batch.patient_id, batch.device_uuid)
    now = datetime.now(timezone.utc)

    created_logs = []
    for point in batch.coordinates:
        recorded_at = point.recorded_at or now
        if recorded_at.tzinfo is None:
            recorded_at = recorded_at.replace(tzinfo=timezone.utc)

        lat = point.latitude if point.is_gps_available else None
        lon = point.longitude if point.is_gps_available else None

        log_entry = LocationLog(
            patient_id=patient_id,
            device_uuid=batch.device_uuid,
            latitude=lat,
            longitude=lon,
            altitude=point.altitude,
            accuracy=point.accuracy,
            speed=point.speed,
            is_gps_available=point.is_gps_available,
            device_battery=point.device_battery,
            recorded_at=recorded_at
        )
        db.add(log_entry)
        created_logs.append(log_entry)

    db.commit()
    for log_entry in created_logs:
        db.refresh(log_entry)

    return created_logs


@router.get("/latest", response_model=LatestLocationOut)
@router.get("/latest/{patient_id}", response_model=LatestLocationOut)
@router.get("/patients/{patient_id}/latest", response_model=LatestLocationOut)
def get_latest_patient_location(
    patient_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get the latest known GPS coordinate of a patient with freshness & stale verification.
    Never invents coordinates when GPS was lost or unavailable.
    """
    target_id = patient_id
    user_role_str = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    if target_id is None:
        if user_role_str == "patient" and current_user.patient_profile:
            target_id = current_user.patient_profile.id
        elif current_user.caregiver_profile and current_user.caregiver_profile.patient_associations:
            target_id = current_user.caregiver_profile.patient_associations[0].patient_id
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="patient_id is required.")

    _check_patient_read_permission(db, target_id, current_user)

    patient = db.query(PatientProfile).filter(PatientProfile.id == target_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient profile {target_id} not found."
        )

    latest = db.query(LocationLog).filter(
        LocationLog.patient_id == target_id
    ).order_by(LocationLog.recorded_at.desc()).first()

    now = datetime.now(timezone.utc)

    # Case 1: No GPS record ever logged
    if not latest:
        return {
            "patient_id": target_id,
            "has_location": False,
            "is_stale": True,
            "status": "unavailable",
            "latest_location": None,
            "message": "No GPS fixes have been recorded for this patient."
        }

    # Case 2: Latest logged entry reports GPS hardware was unavailable
    if not latest.is_gps_available or latest.latitude is None or latest.longitude is None:
        return {
            "patient_id": target_id,
            "has_location": False,
            "is_stale": True,
            "status": "unavailable",
            "latest_location": latest,
            "message": "GPS hardware was unavailable or indoor without satellite lock at last fix."
        }

    # Case 3: Valid GPS fix exists - check staleness threshold
    rec_time = latest.recorded_at
    if rec_time.tzinfo is None:
        rec_time = rec_time.replace(tzinfo=timezone.utc)

    age_minutes = (now - rec_time).total_seconds() / 60.0
    is_stale = age_minutes > STALE_GPS_THRESHOLD_MINUTES

    return {
        "patient_id": patient_id,
        "has_location": True,
        "is_stale": is_stale,
        "status": "stale" if is_stale else "active",
        "latest_location": latest,
        "message": f"Fix age: {int(age_minutes)} minute(s) old." if is_stale else "Real-time fix active."
    }


@router.get("/history/{patient_id}", response_model=List[LocationLogOut])
@router.get("/patients/{patient_id}/history", response_model=List[LocationLogOut])
def get_patient_location_history(
    patient_id: int,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    valid_fixes_only: bool = True,
    skip: int = Query(0, ge=0),
    limit: int = Query(200, ge=1, le=1000),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get historical GPS breadcrumb path for a patient across a specified time period.
    Filters out invalid/unavailable GPS points by default for clean map trajectory plotting.
    """
    _check_patient_read_permission(db, patient_id, current_user)

    query = db.query(LocationLog).filter(LocationLog.patient_id == patient_id)
    if valid_fixes_only:
        query = query.filter(
            LocationLog.is_gps_available == True,  # noqa: E712
            LocationLog.latitude.isnot(None),
            LocationLog.longitude.isnot(None)
        )
    if start_time:
        query = query.filter(LocationLog.recorded_at >= start_time)
    if end_time:
        query = query.filter(LocationLog.recorded_at <= end_time)

    return query.order_by(LocationLog.recorded_at.desc()).offset(skip).limit(limit).all()
