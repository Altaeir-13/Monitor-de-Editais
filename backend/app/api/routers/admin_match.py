from typing import Any, Dict
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.services.notification import match_notices_with_alerts
from app.services.email_dispatcher import dispatch_pending_emails

router = APIRouter()


@router.post("/match-alerts", response_model=Dict[str, int])
def trigger_match(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Manually trigger the notice-alert match routine.
    Requires superuser (admin) role.
    - No token: 401
    - Common user: 403
    - Admin: runs match and returns counters
    """
    return match_notices_with_alerts(db=db)


@router.post("/dispatch-emails", response_model=Dict[str, int])
def trigger_dispatch_emails(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Manually trigger the email dispatch routine for pending notifications.
    Requires superuser (admin) role.
    """
    return dispatch_pending_emails(db=db)
