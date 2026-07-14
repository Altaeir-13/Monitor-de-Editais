from typing import List, Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.institution import Institution
from app.schemas.institution import InstitutionCreate, InstitutionUpdate


def get_institution(db: Session, institution_id: int) -> Optional[Institution]:
    return db.query(Institution).filter(Institution.id == institution_id).first()


def get_institutions(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    *,
    region: Optional[str] = None,
    state: Optional[str] = None,
    administrative_category_code: Optional[int] = None,
    academic_organization_code: Optional[int] = None,
    eligibility_status: Optional[str] = None,
    coverage_status: Optional[str] = None,
    is_active: Optional[bool] = None,
    has_source: Optional[bool] = None,
    manual_review: Optional[bool] = None,
) -> List[Institution]:
    query = db.query(Institution)
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
    if is_active is not None:
        query = query.filter(Institution.is_active.is_(is_active))
    if has_source is True:
        query = query.filter(Institution.monitored_sources.any())
    elif has_source is False:
        query = query.filter(~Institution.monitored_sources.any())
    if manual_review is True:
        query = query.filter(
            (Institution.source_discovery_status == "manual_review")
            | Institution.eligibility_status.contains("manual_review")
        )
    elif manual_review is False:
        query = query.filter(
            or_(
                Institution.source_discovery_status.is_(None),
                Institution.source_discovery_status != "manual_review",
            ),
            or_(
                Institution.eligibility_status.is_(None),
                ~Institution.eligibility_status.contains("manual_review"),
            ),
        )
    return query.order_by(Institution.id).offset(skip).limit(limit).all()


def create_institution(
    db: Session, inst_in: InstitutionCreate
) -> Institution:
    db_obj = Institution(**inst_in.model_dump())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update_institution(
    db: Session,
    db_obj: Institution,
    obj_in: InstitutionUpdate,
) -> Institution:
    update_data = obj_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_obj, field, value)
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete_institution(
    db: Session, db_obj: Institution
) -> Institution:
    db_obj.is_active = False
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj
