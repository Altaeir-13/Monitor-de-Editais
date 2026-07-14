from typing import List, Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.catalog.urls import normalize_url
from app.models.institution import Institution
from app.models.monitored_source import MonitoredSource
from app.schemas.monitored_source import (
    MonitoredSourceCreate,
    MonitoredSourceUpdate,
)


def get_source(
    db: Session, source_id: int
) -> Optional[MonitoredSource]:
    return (
        db.query(MonitoredSource)
        .filter(MonitoredSource.id == source_id)
        .first()
    )


def get_sources(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    *,
    institution_id: Optional[int] = None,
    region: Optional[str] = None,
    state: Optional[str] = None,
    administrative_category_code: Optional[int] = None,
    academic_organization_code: Optional[int] = None,
    eligibility_status: Optional[str] = None,
    coverage_status: Optional[str] = None,
    verification_status: Optional[str] = None,
    institution_active: Optional[bool] = None,
    source_active: Optional[bool] = None,
    manual_review: Optional[bool] = None,
) -> List[MonitoredSource]:
    query = db.query(MonitoredSource)
    joins_institution = any(
        value is not None
        for value in (
            region,
            state,
            administrative_category_code,
            academic_organization_code,
            eligibility_status,
            coverage_status,
            institution_active,
            manual_review,
        )
    )
    if joins_institution:
        query = query.join(Institution)
    if institution_id is not None:
        query = query.filter(MonitoredSource.institution_id == institution_id)
    if region:
        query = query.filter(Institution.region == region)
    if state:
        query = query.filter(Institution.state == state.upper())
    if administrative_category_code is not None:
        query = query.filter(
            Institution.administrative_category_code
            == administrative_category_code
        )
    if academic_organization_code is not None:
        query = query.filter(
            Institution.academic_organization_code == academic_organization_code
        )
    if eligibility_status:
        query = query.filter(Institution.eligibility_status == eligibility_status)
    if coverage_status:
        query = query.filter(
            Institution.source_discovery_status == coverage_status
        )
    if verification_status:
        query = query.filter(
            MonitoredSource.coverage_status == verification_status
        )
    if institution_active is not None:
        query = query.filter(Institution.is_active.is_(institution_active))
    if source_active is not None:
        query = query.filter(MonitoredSource.is_active.is_(source_active))
    if manual_review is True:
        query = query.filter(
            (MonitoredSource.coverage_status == "manual_review")
            | (Institution.source_discovery_status == "manual_review")
            | Institution.eligibility_status.contains("manual_review")
        )
    elif manual_review is False:
        query = query.filter(
            or_(
                MonitoredSource.coverage_status.is_(None),
                MonitoredSource.coverage_status != "manual_review",
            ),
            or_(
                Institution.source_discovery_status.is_(None),
                Institution.source_discovery_status != "manual_review",
            ),
            or_(
                Institution.eligibility_status.is_(None),
                ~Institution.eligibility_status.contains("manual_review"),
            ),
        )
    return query.order_by(MonitoredSource.id).offset(skip).limit(limit).all()


def create_source(
    db: Session, source_in: MonitoredSourceCreate
) -> MonitoredSource:
    values = source_in.model_dump()
    normalized = normalize_url(values["url"])
    values["url"] = normalized
    values["normalized_url"] = normalized
    db_obj = MonitoredSource(**values)
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update_source(
    db: Session,
    db_obj: MonitoredSource,
    obj_in: MonitoredSourceUpdate,
) -> MonitoredSource:
    update_data = obj_in.model_dump(exclude_unset=True)
    if "url" in update_data:
        normalized = normalize_url(update_data["url"])
        update_data["url"] = normalized
        update_data["normalized_url"] = normalized
    for field, value in update_data.items():
        setattr(db_obj, field, value)
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete_source(
    db: Session, db_obj: MonitoredSource
) -> MonitoredSource:
    db_obj.is_active = False
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj
