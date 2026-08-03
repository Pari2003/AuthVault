from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class AuditLogBase(BaseModel):
    user_id: Optional[int] = None
    action: str
    resource: Optional[str] = None
    details: Optional[str] = None
    ip_address: Optional[str] = None

class AuditLogCreate(AuditLogBase):
    pass

class AuditLog(AuditLogBase):
    id: int
    timestamp: datetime
    model_config = ConfigDict(from_attributes=True)
