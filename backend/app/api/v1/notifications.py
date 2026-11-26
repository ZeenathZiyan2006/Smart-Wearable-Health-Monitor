from datetime import datetime, timezone
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.models.notification import InAppNotification
from app.models.user import User
from app.schemas.notification import (
    InAppNotificationCreate,
    InAppNotificationOut,
    NotificationUnreadCountOut,
)

router = APIRouter()


@router.get("", response_model=List[InAppNotificationOut])
def list_notifications(
    unread_only: bool = False,
    notification_type: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Retrieve in-app notifications for the authenticated user.
    """
    query = db.query(InAppNotification).filter(
        InAppNotification.user_id == current_user.id,
        InAppNotification.is_archived == False
    )
    if unread_only:
        query = query.filter(InAppNotification.is_read == False)
    if notification_type:
        query = query.filter(InAppNotification.notification_type == notification_type.lower())

    return query.order_by(InAppNotification.created_at.desc()).offset(offset).limit(limit).all()


@router.get("/unread-count", response_model=NotificationUnreadCountOut)
def get_unread_notification_count(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Returns the count of unread notifications for the user's dashboard badge.
    """
    count = db.query(InAppNotification).filter(
        InAppNotification.user_id == current_user.id,
        InAppNotification.is_read == False,
        InAppNotification.is_archived == False
    ).count()
    return {"unread_count": count, "user_id": current_user.id}


@router.patch("/{notification_id}/read", response_model=InAppNotificationOut)
def mark_notification_read(
    notification_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Mark a single in-app notification as read.
    """
    notif = db.query(InAppNotification).filter(
        InAppNotification.id == notification_id,
        InAppNotification.user_id == current_user.id
    ).first()
    if not notif:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found.")

    if not notif.is_read:
        notif.is_read = True
        notif.read_at = datetime.now(timezone.utc)
        db.add(notif)
        db.commit()
        db.refresh(notif)
    return notif


@router.post("/read-all", status_code=status.HTTP_200_OK)
def mark_all_notifications_read(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Mark all notifications for the current user as read.
    """
    now = datetime.now(timezone.utc)
    count = db.query(InAppNotification).filter(
        InAppNotification.user_id == current_user.id,
        InAppNotification.is_read == False
    ).update({"is_read": True, "read_at": now}, synchronize_session=False)
    db.commit()
    return {"marked_read_count": count}


@router.delete("/{notification_id}", status_code=status.HTTP_200_OK)
def delete_notification(
    notification_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Archive/dismiss an in-app notification.
    """
    notif = db.query(InAppNotification).filter(
        InAppNotification.id == notification_id,
        InAppNotification.user_id == current_user.id
    ).first()
    if not notif:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found.")

    notif.is_archived = True
    db.add(notif)
    db.commit()
    return {"status": "success", "message": "Notification archived."}
