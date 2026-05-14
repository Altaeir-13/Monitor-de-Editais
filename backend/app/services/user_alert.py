from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.user_alert import UserAlert
from app.models.institution import Institution
from app.schemas.user_alert import UserAlertCreate, UserAlertUpdate


def _validate_institution(db: Session, institution_id: int) -> None:
    """Raise 400 if institution does not exist or is inactive."""
    inst = db.query(Institution).filter(Institution.id == institution_id).first()
    if not inst or not inst.is_active:
        raise HTTPException(
            status_code=400,
            detail="Institution does not exist or is not active"
        )


def create_alert(db: Session, user_id: int, alert_in: UserAlertCreate) -> UserAlert:
    if alert_in.institution_id is not None:
        _validate_institution(db, alert_in.institution_id)

    db_obj = UserAlert(
        user_id=user_id,
        keyword=alert_in.keyword,  # already stripped by validator
        institution_id=alert_in.institution_id,
        notice_type=alert_in.notice_type,
        is_active=True,
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def get_alerts(db: Session, user_id: int, skip: int = 0, limit: int = 50) -> List[UserAlert]:
    return (
        db.query(UserAlert)
        .filter(UserAlert.user_id == user_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_alert_by_id(db: Session, user_id: int, alert_id: int) -> Optional[UserAlert]:
    """Returns None if the alert does not exist or belongs to another user."""
    return (
        db.query(UserAlert)
        .filter(UserAlert.id == alert_id, UserAlert.user_id == user_id)
        .first()
    )


def update_alert(db: Session, db_obj: UserAlert, alert_in: UserAlertUpdate) -> UserAlert:
    update_data = alert_in.model_dump(exclude_unset=True)

    # Validate institution_id only when provided and not null
    if "institution_id" in update_data and update_data["institution_id"] is not None:
        _validate_institution(db, update_data["institution_id"])

    # Apply updates (including explicit null to clear optional fields)
    for field, value in update_data.items():
        setattr(db_obj, field, value)

    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def delete_alert(db: Session, db_obj: UserAlert) -> UserAlert:
    """Soft delete — sets is_active = False, never hard deletes."""
    db_obj.is_active = False
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj
