from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api import deps
from app.schemas.institution import InstitutionCreate, InstitutionUpdate, InstitutionResponse
from app.services import institution as institution_service
from app.models.user import User

router = APIRouter()

@router.post("/", response_model=InstitutionResponse)
def create_institution(
    *,
    db: Session = Depends(deps.get_db),
    institution_in: InstitutionCreate,
    current_user: User = Depends(deps.get_current_active_superuser),
) -> Any:
    return institution_service.create_institution(db=db, inst_in=institution_in)

@router.get("/", response_model=List[InstitutionResponse])
def read_institutions(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
) -> Any:
    return institution_service.get_institutions(db=db, skip=skip, limit=limit)

@router.get("/{id}", response_model=InstitutionResponse)
def read_institution(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_user: User = Depends(deps.get_current_active_superuser),
) -> Any:
    institution = institution_service.get_institution(db=db, institution_id=id)
    if not institution:
        raise HTTPException(status_code=404, detail="Institution not found")
    return institution

@router.put("/{id}", response_model=InstitutionResponse)
def update_institution(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    institution_in: InstitutionUpdate,
    current_user: User = Depends(deps.get_current_active_superuser),
) -> Any:
    institution = institution_service.get_institution(db=db, institution_id=id)
    if not institution:
        raise HTTPException(status_code=404, detail="Institution not found")
    return institution_service.update_institution(db=db, db_obj=institution, obj_in=institution_in)

@router.delete("/{id}", response_model=InstitutionResponse)
def delete_institution(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_user: User = Depends(deps.get_current_active_superuser),
) -> Any:
    institution = institution_service.get_institution(db=db, institution_id=id)
    if not institution:
        raise HTTPException(status_code=404, detail="Institution not found")
    return institution_service.delete_institution(db=db, db_obj=institution)
