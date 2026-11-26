import json
from datetime import datetime, timezone
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.models.device import Device, DeviceConnectionHistory
from app.models.health import HealthTelemetry
from app.models.user import PatientCaregiverAssociation, PatientProfile, User, UserRole
from app.schemas.device import (
    DeviceConfigUpdate,
    DeviceConnectionHistoryOut,
    DeviceOut,
    DeviceRegister,
    DeviceSimulateRequest,
)
from app.services.device_adapter import mock_simulator_adapter

router = APIRouter()


def _check_patient_device_access(db: Session, current_user: User, patient_id: int):
    """Verifies that the current user has access to this patient's device."""
    if current_user.role == UserRole.PATIENT.value:
        profile = db.query(PatientProfile).filter(PatientProfile.user_id == current_user.id).first()
        if not profile or profile.id != patient_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access to this patient device is forbidden.")
    elif current_user.role == UserRole.CAREGIVER.value:
        if not current_user.caregiver_profile:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not authorized for this patient.")
        assoc = db.query(PatientCaregiverAssociation).filter(
            PatientCaregiverAssociation.patient_id == patient_id,
            PatientCaregiverAssociation.caregiver_id == current_user.caregiver_profile.id
        ).first()
        if not assoc:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not authorized for this patient.")


@router.post("/pair", response_model=DeviceOut, status_code=status.HTTP_201_CREATED)
def pair_device(
    payload: DeviceRegister,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Register and pair a wearable hardware device with a patient profile.
    """
    target_patient_id = payload.patient_id
    if not target_patient_id:
        if current_user.role == UserRole.PATIENT.value and current_user.patient_profile:
            target_patient_id = current_user.patient_profile.id
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="patient_id is required.")
    else:
        _check_patient_device_access(db, current_user, target_patient_id)

    existing_device = db.query(Device).filter(Device.device_uuid == payload.device_uuid).first()
    now = datetime.now(timezone.utc)

    if existing_device:
        existing_device.patient_id = target_patient_id
        existing_device.status = "connected"
        existing_device.last_sync_at = now
        existing_device.updated_at = now
        device = existing_device
    else:
        device = Device(
            device_uuid=payload.device_uuid,
            device_name=payload.device_name,
            model_type=payload.model_type,
            firmware_version=payload.firmware_version,
            patient_id=target_patient_id,
            status="connected",
            battery_level=100.0,
            is_simulator=payload.is_simulator,
            last_sync_at=now,
            paired_at=now,
        )
        db.add(device)
        db.flush()

    patient = db.query(PatientProfile).filter(PatientProfile.id == target_patient_id).first()
    if patient:
        patient.device_uuid = payload.device_uuid
        patient.device_status = "online"
        patient.last_sync_at = now

    log = DeviceConnectionHistory(
        device_id=device.id,
        event_type="paired",
        details=f"Device paired with patient ID {target_patient_id}",
        recorded_at=now
    )
    db.add(log)
    db.commit()
    db.refresh(device)
    return device


@router.get("", response_model=List[DeviceOut])
def list_devices(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    List all devices registered or accessible to the user.
    """
    if current_user.role == UserRole.PATIENT.value:
        if not current_user.patient_profile:
            return []
        return db.query(Device).filter(Device.patient_id == current_user.patient_profile.id).all()
    elif current_user.role == UserRole.CAREGIVER.value:
        if not current_user.caregiver_profile:
            return []
        assocs = db.query(PatientCaregiverAssociation).filter(
            PatientCaregiverAssociation.caregiver_id == current_user.caregiver_profile.id
        ).all()
        p_ids = [a.patient_id for a in assocs]
        return db.query(Device).filter(Device.patient_id.in_(p_ids)).all()
    else:
        return db.query(Device).all()


@router.get("/{device_id}", response_model=DeviceOut)
def get_device(
    device_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get detailed device information including connection state and firmware version.
    """
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found.")

    if device.patient_id:
        _check_patient_device_access(db, current_user, device.patient_id)
    return device


@router.put("/{device_id}/config", response_model=DeviceOut)
def update_device_config(
    device_id: int,
    config_in: DeviceConfigUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Update wearable device configuration (sampling rates, alert thresholds, sensor toggles).
    """
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found.")

    if device.patient_id:
        _check_patient_device_access(db, current_user, device.patient_id)

    current_cfg = {}
    if device.config_json:
        try:
            current_cfg = json.loads(device.config_json)
        except Exception:
            current_cfg = {}

    updates = config_in.model_dump(exclude_unset=True)
    current_cfg.update(updates)
    device.config_json = json.dumps(current_cfg)
    device.updated_at = datetime.now(timezone.utc)

    db.add(device)
    db.commit()
    db.refresh(device)
    return device


@router.post("/{device_id}/sync", response_model=DeviceOut)
def sync_device(
    device_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Trigger manual device synchronization and refresh connection state.
    """
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found.")

    if device.patient_id:
        _check_patient_device_access(db, current_user, device.patient_id)

    now = datetime.now(timezone.utc)
    device.last_sync_at = now
    device.status = "connected"

    log = DeviceConnectionHistory(
        device_id=device.id,
        event_type="sync",
        details="Manual device synchronization completed successfully.",
        recorded_at=now
    )
    db.add(log)
    db.commit()
    db.refresh(device)
    return device


@router.post("/{device_id}/disconnect", response_model=DeviceOut)
def disconnect_device(
    device_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Marks a device as disconnected and updates hardware status.
    """
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found.")

    if device.patient_id:
        _check_patient_device_access(db, current_user, device.patient_id)

    now = datetime.now(timezone.utc)
    device.status = "disconnected"

    log = DeviceConnectionHistory(
        device_id=device.id,
        event_type="disconnected",
        details="Device disconnected by user request.",
        recorded_at=now
    )
    db.add(log)
    db.commit()
    db.refresh(device)
    return device


@router.get("/{device_id}/history", response_model=List[DeviceConnectionHistoryOut])
def get_device_history(
    device_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Retrieve connection, synchronization, and firmware event history for a device.
    """
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found.")

    if device.patient_id:
        _check_patient_device_access(db, current_user, device.patient_id)

    return db.query(DeviceConnectionHistory).filter(
        DeviceConnectionHistory.device_id == device_id
    ).order_by(DeviceConnectionHistory.recorded_at.desc()).limit(100).all()


@router.post("/{device_id}/simulate", status_code=status.HTTP_201_CREATED)
def simulate_reading(
    device_id: int,
    sim_in: DeviceSimulateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Generate clearly labeled simulated readings for testing and frontend demonstration.
    Does not disguise simulated readings as genuine physical sensor measurements.
    """
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found.")

    if not device.patient_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Device is not associated with any patient.")

    _check_patient_device_access(db, current_user, device.patient_id)

    now = datetime.now(timezone.utc)
    telemetry = HealthTelemetry(
        patient_id=device.patient_id,
        device_uuid=device.device_uuid,
        heart_rate=sim_in.heart_rate,
        spo2=sim_in.spo2,
        temperature=sim_in.temperature,
        step_count=sim_in.step_count or 0,
        fall_detected=sim_in.fall_detected,
        battery_percentage=sim_in.battery_level or 90.0,
        recorded_at=now,
        created_at=now,
    )
    db.add(telemetry)

    device.last_sync_at = now
    device.status = "connected"
    if sim_in.battery_level is not None:
        device.battery_level = sim_in.battery_level

    db.commit()
    return {
        "status": "simulated_reading_recorded",
        "device_uuid": device.device_uuid,
        "is_simulated": True,
        "telemetry_id": telemetry.id,
        "recorded_at": now.isoformat()
    }
