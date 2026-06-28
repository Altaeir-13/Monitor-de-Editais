from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class CrawlerSourceSummary(BaseModel):
    id: int
    name: str
    initials: str


class CrawlerRunResponse(BaseModel):
    id: int
    source_id: int
    source_name: str
    source_url: str
    institution: CrawlerSourceSummary
    status: str
    items_found: int
    new_items: int
    error_message: Optional[str] = None
    started_at: datetime
    finished_at: Optional[datetime] = None


class CrawlerSourceStatusResponse(BaseModel):
    source_id: int
    source_name: str
    source_url: str
    source_type: str
    institution_id: int
    institution_name: str
    institution_initials: str
    is_active: bool
    last_checked_at: Optional[datetime] = None
    last_success_at: Optional[datetime] = None
    last_error_message: Optional[str] = None
    health_status: str
    last_run: Optional[CrawlerRunResponse] = None


class CrawlerStatusResponse(BaseModel):
    total_sources: int
    active_sources: int
    inactive_sources: int
    ok_sources: int
    warning_sources: int
    error_sources: int
    never_checked_sources: int
    total_active_notices: int
    last_run: Optional[CrawlerRunResponse] = None
    last_run_items_found: int
    last_run_new_items: int
