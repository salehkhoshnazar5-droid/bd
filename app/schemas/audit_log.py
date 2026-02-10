from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class AuditLogOut(BaseModel):
    id: int
    user_id: Optional[int] = None
    action: str
    entity: Optional[str] = None
    entity_id: Optional[int] = None
    description: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: datetime

    class Config:
        orm_mode = True