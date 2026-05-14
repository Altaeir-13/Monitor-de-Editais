from typing import Optional
from pydantic import BaseModel, field_validator
from datetime import datetime


class UserAlertCreate(BaseModel):
    keyword: str
    institution_id: Optional[int] = None
    notice_type: Optional[str] = None

    @field_validator("keyword")
    @classmethod
    def keyword_not_empty(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("keyword must not be empty or whitespace-only")
        return stripped


class UserAlertUpdate(BaseModel):
    keyword: Optional[str] = None
    institution_id: Optional[int] = None
    notice_type: Optional[str] = None
    is_active: Optional[bool] = None

    @field_validator("keyword")
    @classmethod
    def keyword_not_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        stripped = v.strip()
        if not stripped:
            raise ValueError("keyword must not be empty or whitespace-only")
        return stripped


class UserAlertResponse(BaseModel):
    id: int
    user_id: int
    keyword: str
    institution_id: Optional[int] = None
    notice_type: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
