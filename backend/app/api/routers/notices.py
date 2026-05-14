from typing import Any, List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.schemas.notice import NoticeResponse, NoticeDetailResponse
from app.services import notice as notice_service

router = APIRouter()


@router.get("/", response_model=List[NoticeResponse])
def list_notices(
    keyword: Optional[str] = None,
    institution_id: Optional[int] = None,
    state: Optional[str] = None,
    notice_type: Optional[str] = None,
    detected_after: Optional[datetime] = None,
    detected_before: Optional[datetime] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    List active notices with optional filters, paginated.
    Public endpoint — no authentication required.
    """
    return notice_service.get_notices(
        db=db,
        keyword=keyword,
        institution_id=institution_id,
        state=state,
        notice_type=notice_type,
        detected_after=detected_after,
        detected_before=detected_before,
        skip=skip,
        limit=limit,
    )


@router.get("/{notice_id}", response_model=NoticeDetailResponse)
def get_notice(
    notice_id: int,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Get a single notice by ID with institution details.
    Returns 404 if the notice does not exist or is inactive.
    Public endpoint — no authentication required.
    """
    notice = notice_service.get_notice_by_id(db=db, notice_id=notice_id)
    if not notice:
        raise HTTPException(status_code=404, detail="Notice not found")
    return notice
