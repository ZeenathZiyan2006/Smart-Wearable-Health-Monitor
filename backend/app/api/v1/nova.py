"""
Nova Universal AI Voice & Clinical Assistant Router
Exposes role-aware, securely authenticated REST endpoints for:
- Role & Permission Context Discovery
- Multilingual Voice & Text Interaction
- Independent Wellbeing Check-ins (Patients & Family Caregivers)
"""
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.database import get_db
from app.api.deps import get_current_active_user
from app.models.user import User, UserRole, PatientProfile
from app.models.nova import NovaWellbeingLog, NovaAuditActionLog
from app.schemas.nova import (
    NovaInteractRequest,
    NovaInteractResponse,
    NovaContextResponse,
    NovaWellbeingCreate,
    NovaWellbeingItem,
)
from app.services.nova_service import NovaAssistantService

router = APIRouter()


@router.get("/context", response_model=NovaContextResponse)
def get_nova_context(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Returns the authenticated user's role-aware Nova capabilities,
    verified authorized patients list, active emergencies, and settings.
    """
    return NovaAssistantService.get_user_context(db, current_user)


@router.post("/interact", response_model=NovaInteractResponse)
def interact_with_nova(
    payload: NovaInteractRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Central role-aware interaction endpoint for Nova.
    Adapts persona and capabilities according to the caller's verified role:
    - Patient: Self-care, daily mood, medication reminder, emergency SOS, family call
    - Family Caregiver: Caregiver wellbeing, authorized patient report, medication status, location
    - Doctor: Clinical trends, AI diagnostic observations, prescription notes review
    - Emergency EMS: Incident status, triage vitals, GPS coordinates, handover logging
    """
    client_ip = request.client.host if request.client else None
    return NovaAssistantService.interact(db, current_user, payload, client_ip=client_ip)


@router.post("/wellbeing", response_model=NovaWellbeingItem, status_code=status.HTTP_201_CREATED)
def record_wellbeing_checkin(
    payload: NovaWellbeingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Records an emotional or physical wellbeing check-in.
    Enforces strict data isolation:
    - Family caregivers' wellbeing data is tagged as is_caregiver_wellbeing=True
      and is NEVER mixed into patient medical records.
    - Patient check-ins are linked to their own profile.
    """
    role = current_user.role or "patient"
    is_caregiver = role in (UserRole.CAREGIVER.value, UserRole.FAMILY.value)
    
    target_pat_id = None
    if not is_caregiver and current_user.patient_profile:
        target_pat_id = current_user.patient_profile.id

    log = NovaWellbeingLog(
        user_id=current_user.id,
        role=role,
        target_patient_id=target_pat_id,
        mood_type=payload.mood_type,
        notes=payload.notes,
        is_caregiver_wellbeing=is_caregiver,
    )
    db.add(log)
    db.commit()
    db.refresh(log)

    return NovaWellbeingItem(
        id=log.id,
        role=log.role,
        mood_type=log.mood_type,
        notes=log.notes,
        is_caregiver_wellbeing=log.is_caregiver_wellbeing,
        created_at=log.created_at.isoformat(),
    )


@router.get("/wellbeing/history", response_model=List[NovaWellbeingItem])
def get_wellbeing_history(
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Returns the user's own wellbeing check-in history.
    Caregivers view only their personal logs; patients view only their own logs.
    """
    logs = db.query(NovaWellbeingLog).filter(
        NovaWellbeingLog.user_id == current_user.id
    ).order_by(desc(NovaWellbeingLog.created_at)).limit(limit).all()

    return [
        NovaWellbeingItem(
            id=l.id,
            role=l.role,
            mood_type=l.mood_type,
            notes=l.notes,
            is_caregiver_wellbeing=l.is_caregiver_wellbeing,
            created_at=l.created_at.isoformat(),
        )
        for l in logs
    ]
