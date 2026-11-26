from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class SystemAuditLogOut(BaseModel):
    id: int
    user_id: Optional[int] = None
    event_type: str
    description: str
    ip_address: Optional[str] = None
    metadata_json: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
