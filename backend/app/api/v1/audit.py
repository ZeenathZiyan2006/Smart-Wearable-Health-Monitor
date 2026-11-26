from datetime import datetime, timezone
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.models.audit import SystemAuditLog
from app.models.user import User, UserRole
from app.schemas.audit import SystemAuditLogOut

router = APIRouter()


class AuditLogCreate(BaseModel):
    event_type: str
    description: str
    metadata_json: Optional[str] = None


@router.get("", response_model=List[SystemAuditLogOut])
def list_audit_logs(
    event_type: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Retrieve system audit trail records. Restricted to Caregiver or Admin users.
    """
    query = db.query(SystemAuditLog)
    if current_user.role == UserRole.PATIENT.value:
        # Patients can only view events where user_id is their own
        query = query.filter(SystemAuditLog.user_id == current_user.id)
    if event_type:
        query = query.filter(SystemAuditLog.event_type == event_type.lower())

    return query.order_by(SystemAuditLog.created_at.desc()).offset(offset).limit(limit).all()


@router.post("/log", response_model=SystemAuditLogOut, status_code=status.HTTP_201_CREATED)
def record_audit_log(
    payload: AuditLogCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Log an important user or system action into the audit trail.
    """
    log = SystemAuditLog(
        user_id=current_user.id,
        event_type=payload.event_type.lower().strip(),
        description=payload.description.strip(),
        metadata_json=payload.metadata_json,
        created_at=datetime.now(timezone.utc)
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log
