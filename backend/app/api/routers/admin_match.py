from typing import Any, Dict
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.crawler.runner import run_crawler
from app.services.notification import match_notices_with_alerts
from app.services.email_dispatcher import dispatch_pending_emails
from app.services.northeast_seed import seed_northeast_institutions

router = APIRouter()


@router.post("/seed-northeast", response_model=Dict[str, int])
def trigger_seed_northeast(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Idempotently seed Northeast public institutions and monitored sources.
    Requires superuser (admin) role.
    """
    return seed_northeast_institutions(db=db)


@router.post("/run-crawler", response_model=Dict[str, int])
def trigger_crawler(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Manually trigger crawling for active monitored sources.
    Requires superuser (admin) role.
    """
    return run_crawler(db=db)


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