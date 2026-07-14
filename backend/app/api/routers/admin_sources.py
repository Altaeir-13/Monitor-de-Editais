from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.schemas.monitored_source import (
    MonitoredSourceCreate,
    MonitoredSourceResponse,
    MonitoredSourceUpdate,
)
from app.services import institution as institution_service
from app.services import monitored_source as source_service


router = APIRouter()


@router.post("/", response_model=MonitoredSourceResponse)
def create_source(
    *,
    db: Session = Depends(deps.get_db),
    source_in: MonitoredSourceCreate,
    current_user: User = Depends(deps.get_current_active_superuser),
) -> Any:
    institution = institution_service.get_institution(
        db=db,
        institution_id=source_in.institution_id,
    )
    if not institution:
        raise HTTPException(
            status_code=400,
            detail="Institution does not exist",
        )
    return source_service.create_source(db=db, source_in=source_in)


@router.get("/", response_model=List[MonitoredSourceResponse])
def read_sources(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    institution_id: Optional[int] = Query(default=None),
    region: Optional[str] = Query(default=None),
    state: Optional[str] = Query(default=None, min_length=2, max_length=2),
    administrative_category_code: Optional[int] = Query(default=None),
    academic_organization_code: Optional[int] = Query(default=None),
    eligibility_status: Optional[str] = Query(default=None),
    coverage_status: Optional[str] = Query(default=None),
    verification_status: Optional[str] = Query(default=None),
    institution_active: Optional[bool] = Query(default=None),
    source_active: Optional[bool] = Query(default=None),
    manual_review: Optional[bool] = Query(default=None),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
) -> Any:
    return source_service.get_sources(
        db=db,
        skip=skip,
        limit=limit,
        institution_id=institution_id,
        region=region,
        state=state,
        administrative_category_code=administrative_category_code,
        academic_organization_code=academic_organization_code,
        eligibility_status=eligibility_status,
        coverage_status=coverage_status,
        verification_status=verification_status,
        institution_active=institution_active,
        source_active=source_active,
        manual_review=manual_review,
    )


@router.get("/{id}", response_model=MonitoredSourceResponse)
def read_source(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_user: User = Depends(deps.get_current_active_superuser),
) -> Any:
    source = source_service.get_source(db=db, source_id=id)
    if not source:
        raise HTTPException(
            status_code=404,
            detail="MonitoredSource not found",
        )
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
        raise HTTPException(
            status_code=404,
            detail="MonitoredSource not found",
        )
    if source_in.institution_id is not None:
        institution = institution_service.get_institution(
            db=db,
            institution_id=source_in.institution_id,
        )
        if not institution:
            raise HTTPException(
                status_code=400,
                detail="Institution does not exist",
            )
    return source_service.update_source(
        db=db,
        db_obj=source,
        obj_in=source_in,
    )


@router.delete("/{id}", response_model=MonitoredSourceResponse)
def delete_source(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_user: User = Depends(deps.get_current_active_superuser),
) -> Any:
    source = source_service.get_source(db=db, source_id=id)
    if not source:
        raise HTTPException(
            status_code=404,
            detail="MonitoredSource not found",
        )
    return source_service.delete_source(db=db, db_obj=source)
