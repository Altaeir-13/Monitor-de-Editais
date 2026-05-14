from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.institution import Institution
from app.schemas.institution import InstitutionCreate, InstitutionUpdate

def get_institution(db: Session, institution_id: int) -> Optional[Institution]:
    return db.query(Institution).filter(Institution.id == institution_id).first()

def get_institutions(db: Session, skip: int = 0, limit: int = 100) -> List[Institution]:
    return db.query(Institution).offset(skip).limit(limit).all()

def create_institution(db: Session, inst_in: InstitutionCreate) -> Institution:
    db_obj = Institution(
        name=inst_in.name,
        initials=inst_in.initials,
        state=inst_in.state,
        official_site_url=inst_in.official_site_url,
        logo_url=inst_in.logo_url,
        is_active=inst_in.is_active
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def update_institution(db: Session, db_obj: Institution, obj_in: InstitutionUpdate) -> Institution:
    update_data = obj_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_obj, field, value)
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def delete_institution(db: Session, db_obj: Institution) -> Institution:
    db_obj.is_active = False
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj
