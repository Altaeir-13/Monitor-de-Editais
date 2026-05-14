from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api import deps
from app.schemas.monitored_source import MonitoredSourceCreate, MonitoredSourceUpdate, MonitoredSourceResponse
from app.services import monitored_source as source_service
from app.services import institution as institution_service
from app.models.user import User

router = APIRouter()

@router.post("/", response_model=MonitoredSourceResponse)
def create_source(
    *,
    db: Session = Depends(deps.get_db),
    source_in: MonitoredSourceCreate,
    current_user: User = Depends(deps.get_current_active_superuser),
) -> Any:
    institution = institution_service.get_institution(db=db, institution_id=source_in.institution_id)
    if not institution:
        raise HTTPException(status_code=400, detail="Institution does not exist")
    return source_service.create_source(db=db, source_in=source_in)

@router.get("/", response_model=List[MonitoredSourceResponse])
def read_sources(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
) -> Any:
    return source_service.get_sources(db=db, skip=skip, limit=limit)

@router.get("/{id}", response_model=MonitoredSourceResponse)
def read_source(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_user: User = Depends(deps.get_current_active_superuser),
) -> Any:
    source = source_service.get_source(db=db, source_id=id)
    if not source:
        raise HTTPException(status_code=404, detail="MonitoredSource not found")
    return source

@router.put("/{id}", response_model=MonitoredSourceResponse)
def update_source(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    source_in: MonitoredSourceUpdate,
    current_user: User = Depends(deps.get_current_active_superuser),
) -> Any:
    source = source_service.get_source(db=db, source_id=id)
    if not source:
        raise HTTPException(status_code=404, detail="MonitoredSource not found")
    if source_in.institution_id is not None:
        institution = institution_service.get_institution(db=db, institution_id=source_in.institution_id)
        if not institution:
            raise HTTPException(status_code=400, detail="Institution does not exist")
    return source_service.update_source(db=db, db_obj=source, obj_in=source_in)

@router.delete("/{id}", response_model=MonitoredSourceResponse)
def delete_source(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_user: User = Depends(deps.get_current_active_superuser),
) -> Any:
    source = source_service.get_source(db=db, source_id=id)
    if not source:
        raise HTTPException(status_code=404, detail="MonitoredSource not found")
    return source_service.delete_source(db=db, db_obj=source)
