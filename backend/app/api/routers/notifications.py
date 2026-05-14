from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.schemas.notification import NotificationResponse, NotificationDetailResponse
from app.services import notification as notification_service

router = APIRouter()


@router.get("/", response_model=List[NotificationResponse])
def list_notifications(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """List all notifications belonging to the authenticated user."""
    return notification_service.get_notifications(
        db=db, user_id=current_user.id, skip=skip, limit=limit
    )


@router.get("/{notification_id}", response_model=NotificationDetailResponse)
def get_notification(
    notification_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """Get a specific notification with notice detail. Returns 404 if not owned by the user."""
    notification = notification_service.get_notification_by_id(
        db=db, user_id=current_user.id, notification_id=notification_id
    )
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    return notification
