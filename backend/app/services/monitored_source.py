from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.monitored_source import MonitoredSource
from app.schemas.monitored_source import MonitoredSourceCreate, MonitoredSourceUpdate

def get_source(db: Session, source_id: int) -> Optional[MonitoredSource]:
    return db.query(MonitoredSource).filter(MonitoredSource.id == source_id).first()

def get_sources(db: Session, skip: int = 0, limit: int = 100) -> List[MonitoredSource]:
    return db.query(MonitoredSource).offset(skip).limit(limit).all()

def create_source(db: Session, source_in: MonitoredSourceCreate) -> MonitoredSource:
    db_obj = MonitoredSource(
        institution_id=source_in.institution_id,
        name=source_in.name,
        url=source_in.url,
        source_type=source_in.source_type,
        check_frequency_minutes=source_in.check_frequency_minutes,
        is_active=source_in.is_active
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def update_source(db: Session, db_obj: MonitoredSource, obj_in: MonitoredSourceUpdate) -> MonitoredSource:
    update_data = obj_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_obj, field, value)
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def delete_source(db: Session, db_obj: MonitoredSource) -> MonitoredSource:
    db_obj.is_active = False
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj
