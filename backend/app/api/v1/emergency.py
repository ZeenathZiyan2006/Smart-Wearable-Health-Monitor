from datetime import datetime, timezone
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from app.api.deps import (
    get_current_active_user,
    get_db,
    get_optional_current_user,
)
from app.api.v1.health import _check_patient_read_permission, _resolve_patient_id
from app.models.emergency import EmergencyAlert, EscalationAuditLog
from app.models.location import LocationLog
from app.models.notification import InAppNotification
from app.models.user import (
    CaregiverProfile,
    PatientCaregiverAssociation,
    PatientProfile,
    User,
    UserRole,
)
from app.schemas.emergency import (
    AlertAcknowledgeRequest,
    AlertRejectRequest,
    AssistanceRequestCreate,
    EmergencyAlertCreate,
    EmergencyAlertOut,
    EscalationAuditLogOut,
)
from app.workers.tasks import dispatch_emergency_escalation
from app.services.voice.emergency_dictionary import get_draft_emergency_phrase

router = APIRouter()


def _check_caregiver_response_permission(
    db: Session,
    alert: EmergencyAlert,
    current_user: User
) -> None:
    """
    Enforces security rule: Only assigned caregivers (or admins) are authorized
    to acknowledge, reject, or resolve a patient's emergency alert.
    """
    if current_user.role == UserRole.ADMIN.value:
        return

    if current_user.role != UserRole.CAREGIVER.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Only assigned caregivers can acknowledge or reject emergency alerts."
        )

    if not current_user.caregiver_profile:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Caregiver profile not found."
        )

    assoc = db.query(PatientCaregiverAssociation).filter(
        PatientCaregiverAssociation.patient_id == alert.patient_id,
        PatientCaregiverAssociation.caregiver_id == current_user.caregiver_profile.id
    ).first()

    if not assoc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You are not an assigned caregiver for this patient."
        )


def _populate_latest_gps_if_missing(
    db: Session,
    patient_id: int,
    latitude: Optional[float],
    longitude: Optional[float]
) -> tuple[Optional[float], Optional[float], Optional[float]]:
    """Automatically attaches the patient's latest known GPS fix if coordinates were omitted."""
    if latitude is not None and longitude is not None:
        return latitude, longitude, None

    latest_loc = db.query(LocationLog).filter(
        LocationLog.patient_id == patient_id,
        LocationLog.is_gps_available == True,  # noqa: E712
        LocationLog.latitude.isnot(None),
        LocationLog.longitude.isnot(None)
    ).order_by(LocationLog.recorded_at.desc()).first()

    if latest_loc:
        return latest_loc.latitude, latest_loc.longitude, latest_loc.accuracy

    return None, None, None


# -----------------------------------------------------------------------------
# Alert Trigger Endpoints
# -----------------------------------------------------------------------------
@router.post("/sos", response_model=EmergencyAlertOut, status_code=status.HTTP_201_CREATED)
def trigger_manual_or_fall_sos(
    alert_in: EmergencyAlertCreate,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Trigger a critical emergency SOS alert (manual button press or fall detection).
    Instantly initiates multi-tier caregiver notification escalation ladder.
    """
    patient_id = _resolve_patient_id(db, current_user, alert_in.patient_id, alert_in.device_uuid)

    lat, lon, acc = _populate_latest_gps_if_missing(db, patient_id, alert_in.latitude, alert_in.longitude)

    now = datetime.now(timezone.utc)
    patient_rec = db.query(PatientProfile).filter(PatientProfile.id == patient_id).first()
    pref_lang = (patient_rec.user.preferred_language if patient_rec and patient_rec.user else "en")
    phrase_key = "FALL_DETECTED" if alert_in.alert_type == "fall_detected" else "EMERGENCY_TRIGGERED"
    localized_summary = getattr(alert_in, 'translated_summary', None) or get_draft_emergency_phrase(phrase_key, pref_lang)

    alert = EmergencyAlert(
        patient_id=patient_id,
        device_uuid=alert_in.device_uuid,
        alert_type=alert_in.alert_type,
        severity=alert_in.severity or "critical",
        status="triggered",
        current_escalation_tier=1,
        latitude=lat,
        longitude=lon,
        location_accuracy=alert_in.location_accuracy or acc,
        voice_transcript=alert_in.voice_transcript,
        assistance_message=alert_in.assistance_message,
        translated_summary=localized_summary,
        detected_language=pref_lang,
        created_at=now
    )
    db.add(alert)

    # Log in-app notification for patient and caregiver notification centers
    if current_user:
        notif = InAppNotification(
            user_id=current_user.id,
            title="🚨 Emergency SOS Broadcast Transmitted",
            body=f"SOS alert #{alert.id or ''} triggered. Coordinates: ({lat or 'GPS acquiring'}, {lon or 'GPS acquiring'}). Primary & secondary caregiver escalation ladder engaged.",
            notification_type="emergency",
            severity="emergency",
            is_read=False,
            created_at=now
        )
        db.add(notif)

    db.commit()
    db.refresh(alert)

    # Initiate background escalation ladder
    dispatch_emergency_escalation(alert.id, initial_tier=1)

    db.refresh(alert)
    return alert


@router.post("/assistance", response_model=EmergencyAlertOut, status_code=status.HTTP_201_CREATED)
def request_assistance_not_okay(
    req_in: AssistanceRequestCreate,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Trigger an 'I'm Not Okay' assistance request with optional symptom description.
    Initiates caregiver notification escalation.
    """
    patient_id = _resolve_patient_id(db, current_user, req_in.patient_id, req_in.device_uuid)

    lat, lon, acc = _populate_latest_gps_if_missing(db, patient_id, req_in.latitude, req_in.longitude)

    now = datetime.now(timezone.utc)
    alert = EmergencyAlert(
        patient_id=patient_id,
        device_uuid=req_in.device_uuid,
        alert_type="not_okay_assistance",
        severity=req_in.severity or "high",
        status="triggered",
        current_escalation_tier=1,
        latitude=lat,
        longitude=lon,
        location_accuracy=acc,
        assistance_message=req_in.message or "Patient requested assistance ('I'm Not Okay')",
        created_at=now
    )
    db.add(alert)

    # Log in-app notification for patient and caregiver notification centers
    if current_user:
        notif = InAppNotification(
            user_id=current_user.id,
            title="🚨 Emergency SOS Broadcast Transmitted",
            body=f"SOS alert #{alert.id or ''} triggered. Coordinates: ({lat or 'GPS acquiring'}, {lon or 'GPS acquiring'}). Primary & secondary caregiver escalation ladder engaged.",
            notification_type="emergency",
            severity="emergency",
            is_read=False,
            created_at=now
        )
        db.add(notif)

    db.commit()
    db.refresh(alert)

    # Dispatch to Tier 1 caregiver
    dispatch_emergency_escalation(alert.id, initial_tier=1)

    db.refresh(alert)
    return alert


# -----------------------------------------------------------------------------
# Alert Management & History Endpoints
# -----------------------------------------------------------------------------
@router.get("/alerts", response_model=List[EmergencyAlertOut])
def list_emergency_alerts(
    patient_id: Optional[int] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    severity: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Retrieve emergency alerts history. Filterable by patient, status, and severity.
    Protected by role-based access control.
    """
    query = db.query(EmergencyAlert).options(joinedload(EmergencyAlert.audit_logs))

    if current_user.role == UserRole.PATIENT.value:
        if not current_user.patient_profile:
            return []
        query = query.filter(EmergencyAlert.patient_id == current_user.patient_profile.id)
    elif current_user.role == UserRole.CAREGIVER.value:
        if not current_user.caregiver_profile:
            return []
        # Filter to only assigned patients
        assigned_patient_ids = [
            a.patient_id for a in db.query(PatientCaregiverAssociation.patient_id).filter(
                PatientCaregiverAssociation.caregiver_id == current_user.caregiver_profile.id
            ).all()
        ]
        if patient_id:
            if patient_id not in assigned_patient_ids:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: You are not assigned to this patient."
                )
            query = query.filter(EmergencyAlert.patient_id == patient_id)
        else:
            query = query.filter(EmergencyAlert.patient_id.in_(assigned_patient_ids))
    elif current_user.role == UserRole.ADMIN.value:
        if patient_id:
            query = query.filter(EmergencyAlert.patient_id == patient_id)

    if status_filter:
        query = query.filter(EmergencyAlert.status == status_filter)
    if severity:
        query = query.filter(EmergencyAlert.severity == severity)

    return query.order_by(EmergencyAlert.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/{alert_id}", response_model=EmergencyAlertOut)
def get_alert_details(
    alert_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get detailed information about an emergency alert including full audit log.
    """
    alert = db.query(EmergencyAlert).options(
        joinedload(EmergencyAlert.audit_logs)
    ).filter(EmergencyAlert.id == alert_id).first()

    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Emergency alert {alert_id} not found."
        )

    _check_patient_read_permission(db, alert.patient_id, current_user)
    return alert


@router.post("/{alert_id}/acknowledge", response_model=EmergencyAlertOut)
def acknowledge_alert(
    alert_id: int,
    ack_in: AlertAcknowledgeRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Caregiver acknowledges emergency alert. Immediately halts the escalation ladder
    and logs the response in the audit trail.
    """
    alert = db.query(EmergencyAlert).filter(EmergencyAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Emergency alert {alert_id} not found."
        )

    _check_caregiver_response_permission(db, alert, current_user)

    now = datetime.now(timezone.utc)
    alert.status = "acknowledged"
    alert.acknowledged_by_id = current_user.id
    alert.acknowledged_at = now
    if ack_in.notes:
        alert.resolution_notes = ack_in.notes

    # Add audit log for acknowledgment
    audit = EscalationAuditLog(
        alert_id=alert.id,
        tier=alert.current_escalation_tier,
        notified_caregiver_id=current_user.caregiver_profile.id if current_user.caregiver_profile else None,
        notification_channel="system",
        provider="system_auth",
        recipient_address=current_user.email,
        status="acknowledged",
        message_payload=f"Acknowledged by {current_user.full_name}: {ack_in.notes or 'No notes'}",
        sent_at=now
    )
    db.add(audit)
    db.commit()
    db.refresh(alert)
    return alert


@router.post("/{alert_id}/reject", response_model=EmergencyAlertOut)
def reject_alert(
    alert_id: int,
    reject_in: AlertRejectRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Caregiver marks alert as false alarm or rejects it. Halts escalation ladder
    and records the rejection reason in the audit trail.
    """
    alert = db.query(EmergencyAlert).filter(EmergencyAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Emergency alert {alert_id} not found."
        )

    _check_caregiver_response_permission(db, alert, current_user)

    now = datetime.now(timezone.utc)
    alert.status = "rejected"
    alert.rejected_by_id = current_user.id
    alert.rejected_at = now
    alert.rejection_reason = reject_in.reason

    audit = EscalationAuditLog(
        alert_id=alert.id,
        tier=alert.current_escalation_tier,
        notified_caregiver_id=current_user.caregiver_profile.id if current_user.caregiver_profile else None,
        notification_channel="system",
        provider="system_auth",
        recipient_address=current_user.email,
        status="rejected",
        message_payload=f"Rejected / False Alarm by {current_user.full_name}: {reject_in.reason}",
        sent_at=now
    )
    db.add(audit)
    db.commit()
    db.refresh(alert)
    return alert


@router.get("/{alert_id}/escalation-history", response_model=List[EscalationAuditLogOut])
def get_alert_escalation_history(
    alert_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Retrieve chronological audit trail of all escalation steps, dispatches, and responses.
    """
    alert = db.query(EmergencyAlert).filter(EmergencyAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Emergency alert {alert_id} not found."
        )

    _check_patient_read_permission(db, alert.patient_id, current_user)

    logs = db.query(EscalationAuditLog).filter(
        EscalationAuditLog.alert_id == alert_id
    ).order_by(EscalationAuditLog.sent_at.asc()).all()

    return logs
