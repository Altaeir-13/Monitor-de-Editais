from typing import Optional
from pydantic import BaseModel
from datetime import datetime

class InstitutionBase(BaseModel):
    name: str
    initials: str
    state: str
    official_site_url: str
    logo_url: Optional[str] = None
    is_active: bool = True

class InstitutionCreate(InstitutionBase):
    pass

class InstitutionUpdate(BaseModel):
    name: Optional[str] = None
    initials: Optional[str] = None
    state: Optional[str] = None
    official_site_url: Optional[str] = None
    logo_url: Optional[str] = None
    is_active: Optional[bool] = None

class InstitutionInDBBase(InstitutionBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class InstitutionResponse(InstitutionInDBBase):
    pass
