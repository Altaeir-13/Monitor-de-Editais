from typing import List, Optional, Dict
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_

from app.models.user_alert import UserAlert
from app.models.notice import Notice
from app.models.notification import Notification


def get_notifications(
    db: Session,
    user_id: int,
    skip: int = 0,
    limit: int = 50,
) -> List[Notification]:
    return (
        db.query(Notification)
        .filter(Notification.user_id == user_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_notification_by_id(
    db: Session,
    user_id: int,
    notification_id: int,
) -> Optional[Notification]:
    """Returns None if notification does not exist or belongs to another user."""
    return (
        db.query(Notification)
        .options(joinedload(Notification.notice))
        .filter(
            Notification.id == notification_id,
            Notification.user_id == user_id,
        )
        .first()
    )


def match_notices_with_alerts(db: Session) -> Dict[str, int]:
    """
    Cross-match active UserAlerts against active Notices and create
    Notification records (status='pending') for new matches.

    Duplicate prevention strategy: load all existing (user_id, notice_id)
    pairs into a set in memory before the loop, then only insert pairs not
    already present. A single db.commit() is performed at the end.

    Returns a dict with match statistics.
    """
    alerts_checked = 0
    notices_checked = 0
    notifications_created = 0
    duplicates_skipped = 0

    # 1. Load all active alerts
    active_alerts = (
        db.query(UserAlert)
        .filter(UserAlert.is_active == True)
        .all()
    )
    alerts_checked = len(active_alerts)

    if not active_alerts:
        return {
            "alerts_checked": alerts_checked,
            "notices_checked": notices_checked,
            "notifications_created": notifications_created,
            "duplicates_skipped": duplicates_skipped,
        }

    # 2. Pre-load all existing (user_id, notice_id) pairs into a set in memory
    existing_pairs = set(
        db.query(Notification.user_id, Notification.notice_id).all()
    )

    new_notifications = []

    # 3. Process each alert
    for alert in active_alerts:
        # Build base query for active notices
        notice_query = db.query(Notice).filter(Notice.is_active == True)

        # Keyword match (mandatory): apply to title and description
        keyword_filter = f"%{alert.keyword}%"
        notice_query = notice_query.filter(
            or_(
                Notice.title.ilike(keyword_filter),
                Notice.description.ilike(keyword_filter),
            )
        )

        # Optional institution_id filter
        if alert.institution_id is not None:
            notice_query = notice_query.filter(
                Notice.institution_id == alert.institution_id
            )

        # Optional notice_type filter
        if alert.notice_type is not None:
            notice_query = notice_query.filter(
                Notice.notice_type == alert.notice_type
            )

        matched_notices = notice_query.all()
        notices_checked += len(matched_notices)

        for notice in matched_notices:
            pair = (alert.user_id, notice.id)
            if pair in existing_pairs:
                duplicates_skipped += 1
            else:
                new_notifications.append(
                    Notification(
                        user_id=alert.user_id,
                        notice_id=notice.id,
                        status="pending",
                    )
                )
                existing_pairs.add(pair)  # prevent in-batch duplicates
                notifications_created += 1

    # 4. Bulk insert and single commit
    if new_notifications:
        db.add_all(new_notifications)
        db.commit()

    return {
        "alerts_checked": alerts_checked,
        "notices_checked": notices_checked,
        "notifications_created": notifications_created,
        "duplicates_skipped": duplicates_skipped,
    }
