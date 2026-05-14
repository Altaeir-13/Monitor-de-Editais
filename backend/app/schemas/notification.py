from typing import Optional
from pydantic import BaseModel
from datetime import datetime

from app.schemas.notice import NoticeResponse


class NotificationResponse(BaseModel):
    id: int
    user_id: int
    notice_id: int
    status: str
    sent_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationDetailResponse(NotificationResponse):
    notice: Optional[NoticeResponse] = None

    class Config:
        from_attributes = True
