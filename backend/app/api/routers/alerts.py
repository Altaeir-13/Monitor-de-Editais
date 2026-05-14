from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.schemas.user_alert import UserAlertCreate, UserAlertUpdate, UserAlertResponse
from app.services import user_alert as user_alert_service

router = APIRouter()


@router.post("/", response_model=UserAlertResponse)
def create_alert(
    *,
    db: Session = Depends(deps.get_db),
    alert_in: UserAlertCreate,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """Create a new alert for the authenticated user."""
    return user_alert_service.create_alert(db=db, user_id=current_user.id, alert_in=alert_in)


@router.get("/", response_model=List[UserAlertResponse])
def list_alerts(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """List all alerts belonging to the authenticated user."""
    return user_alert_service.get_alerts(db=db, user_id=current_user.id, skip=skip, limit=limit)


@router.get("/{alert_id}", response_model=UserAlertResponse)
def get_alert(
    alert_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """Get a specific alert. Returns 404 if not owned by the authenticated user."""
    alert = user_alert_service.get_alert_by_id(db=db, user_id=current_user.id, alert_id=alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@router.put("/{alert_id}", response_model=UserAlertResponse)
def update_alert(
    *,
    alert_id: int,
    alert_in: UserAlertUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """Partially update an alert owned by the authenticated user."""
    alert = user_alert_service.get_alert_by_id(db=db, user_id=current_user.id, alert_id=alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return user_alert_service.update_alert(db=db, db_obj=alert, alert_in=alert_in)


@router.delete("/{alert_id}", response_model=UserAlertResponse)
def delete_alert(
    alert_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """Soft-delete an alert (sets is_active=False). Returns 404 if not owned by the user."""
    alert = user_alert_service.get_alert_by_id(db=db, user_id=current_user.id, alert_id=alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return user_alert_service.delete_alert(db=db, db_obj=alert)
