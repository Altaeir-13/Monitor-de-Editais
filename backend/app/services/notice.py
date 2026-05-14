from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_

from app.models.notice import Notice
from app.models.institution import Institution


def get_notices(
    db: Session,
    keyword: Optional[str] = None,
    institution_id: Optional[int] = None,
    state: Optional[str] = None,
    notice_type: Optional[str] = None,
    detected_after: Optional[datetime] = None,
    detected_before: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 50,
) -> List[Notice]:
    """
    Retrieve a paginated list of active notices with optional filters.
    Always filters by is_active == True.
    Orders by detected_at desc (most recent first).
    """
    query = db.query(Notice).filter(Notice.is_active == True)

    if keyword:
        keyword_filter = f"%{keyword}%"
        query = query.filter(
            or_(
                Notice.title.ilike(keyword_filter),
                Notice.description.ilike(keyword_filter),
            )
        )

    if institution_id is not None:
        query = query.filter(Notice.institution_id == institution_id)

    if state:
        query = query.join(Institution).filter(Institution.state == state)

    if notice_type:
        query = query.filter(Notice.notice_type == notice_type)

    if detected_after:
        query = query.filter(Notice.detected_at >= detected_after)

    if detected_before:
        query = query.filter(Notice.detected_at <= detected_before)

    query = query.order_by(Notice.detected_at.desc())
    query = query.offset(skip).limit(limit)

    return query.all()


def get_notice_by_id(db: Session, notice_id: int) -> Optional[Notice]:
    """
    Retrieve a single active notice by ID.
    Uses joinedload to eagerly load the institution relationship,
    avoiding N+1 queries.
    Returns None if the notice doesn't exist or is inactive.
    """
    return (
        db.query(Notice)
        .options(joinedload(Notice.institution))
        .filter(Notice.id == notice_id, Notice.is_active == True)
        .first()
    )
