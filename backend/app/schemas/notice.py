from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class InstitutionBasicResponse(BaseModel):
    id: int
    name: str
    initials: str
    state: str
    official_site_url: str

    class Config:
        from_attributes = True


class NoticeResponse(BaseModel):
    id: int
    institution_id: int
    source_id: int
    title: str
    url: str
    notice_type: str
    detected_at: datetime
    publication_date: Optional[datetime] = None
    description: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True


class NoticeDetailResponse(NoticeResponse):
    institution: Optional[InstitutionBasicResponse] = None

    class Config:
        from_attributes = True
