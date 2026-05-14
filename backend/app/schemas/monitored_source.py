from typing import Optional
from pydantic import BaseModel
from datetime import datetime

class MonitoredSourceBase(BaseModel):
    institution_id: int
    name: str
    url: str
    source_type: str
    check_frequency_minutes: int
    is_active: bool = True

class MonitoredSourceCreate(MonitoredSourceBase):
    pass

class MonitoredSourceUpdate(BaseModel):
    institution_id: Optional[int] = None
    name: Optional[str] = None
    url: Optional[str] = None
    source_type: Optional[str] = None
    check_frequency_minutes: Optional[int] = None
    is_active: Optional[bool] = None

class MonitoredSourceInDBBase(MonitoredSourceBase):
    id: int
    last_checked_at: Optional[datetime] = None
    last_success_at: Optional[datetime] = None
    last_error_message: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class MonitoredSourceResponse(MonitoredSourceInDBBase):
    pass
