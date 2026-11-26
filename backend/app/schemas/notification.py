from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class InAppNotificationOut(BaseModel):
    id: int
    user_id: int
    title: str
    body: str
    notification_type: str
    severity: str
    data_json: Optional[str] = None
    is_read: bool
    read_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotificationUnreadCountOut(BaseModel):
    unread_count: int
    user_id: int


class InAppNotificationCreate(BaseModel):
    user_id: int
    title: str
    body: str
    notification_type: str = "health"
    severity: str = "info"
    data_json: Optional[str] = None
