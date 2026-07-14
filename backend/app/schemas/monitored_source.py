from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class MonitoredSourceBase(BaseModel):
    institution_id: int
    name: str
    url: str
    source_type: str
    check_frequency_minutes: int = 1440
    is_active: bool = False
    catalog_source_id: Optional[str] = None
    normalized_url: Optional[str] = None
    content_type: Optional[str] = None
    recommended_spider: Optional[str] = None
    coverage_status: Optional[str] = None
    last_verified_at: Optional[datetime] = None
    verification_http_status: Optional[int] = None
    verification_final_url: Optional[str] = None
    verification_redirect_chain: Optional[str] = None
    verification_page_title: Optional[str] = None
    verification_evidence: Optional[str] = None
    verification_notes: Optional[str] = None
    priority: Optional[int] = None
    notice_categories: Optional[str] = None
    capture_validated_at: Optional[datetime] = None
    capture_evidence: Optional[str] = None


class MonitoredSourceCreate(MonitoredSourceBase):
    pass


class MonitoredSourceUpdate(BaseModel):
    institution_id: Optional[int] = None
    name: Optional[str] = None
    url: Optional[str] = None
    source_type: Optional[str] = None
    check_frequency_minutes: Optional[int] = None
    is_active: Optional[bool] = None
    catalog_source_id: Optional[str] = None
    content_type: Optional[str] = None
    recommended_spider: Optional[str] = None
    coverage_status: Optional[str] = None
    last_verified_at: Optional[datetime] = None
    verification_http_status: Optional[int] = None
    verification_final_url: Optional[str] = None
    verification_redirect_chain: Optional[str] = None
    verification_page_title: Optional[str] = None
    verification_evidence: Optional[str] = None
    verification_notes: Optional[str] = None
    priority: Optional[int] = None
    notice_categories: Optional[str] = None
    capture_validated_at: Optional[datetime] = None
    capture_evidence: Optional[str] = None


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
