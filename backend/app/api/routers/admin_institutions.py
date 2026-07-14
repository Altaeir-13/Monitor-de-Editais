from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.schemas.institution import (
    InstitutionCreate,
    InstitutionResponse,
    InstitutionUpdate,
)
from app.services import institution as institution_service


router = APIRouter()


@router.post("/", response_model=InstitutionResponse)
def create_institution(
    *,
    db: Session = Depends(deps.get_db),
    institution_in: InstitutionCreate,
    current_user: User = Depends(deps.get_current_active_superuser),
) -> Any:
    return institution_service.create_institution(
        db=db,
        inst_in=institution_in,
    )


@router.get("/", response_model=List[InstitutionResponse])
def read_institutions(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    region: Optional[str] = Query(default=None),
    state: Optional[str] = Query(default=None, min_length=2, max_length=2),
    administrative_category_code: Optional[int] = Query(default=None),
    academic_organization_code: Optional[int] = Query(default=None),
    eligibility_status: Optional[str] = Query(default=None),
    coverage_status: Optional[str] = Query(default=None),
    is_active: Optional[bool] = Query(default=None),
    has_source: Optional[bool] = Query(default=None),
    manual_review: Optional[bool] = Query(default=None),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
) -> Any:
    return institution_service.get_institutions(
        db=db,
        skip=skip,
        limit=limit,
        region=region,
        state=state,
        administrative_category_code=administrative_category_code,
        academic_organization_code=academic_organization_code,
        eligibility_status=eligibility_status,
        coverage_status=coverage_status,
        is_active=is_active,
        has_source=has_source,
        manual_review=manual_review,
    )


@router.get("/{id}", response_model=InstitutionResponse)
def read_institution(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_user: User = Depends(deps.get_current_active_superuser),
) -> Any:
    institution = institution_service.get_institution(
        db=db,
        institution_id=id,
    )
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
    institution = institution_service.get_institution(
        db=db,
        institution_id=id,
    )
    if not institution:
        raise HTTPException(status_code=404, detail="Institution not found")
    return institution_service.update_institution(
        db=db,
        db_obj=institution,
        obj_in=institution_in,
    )


@router.delete("/{id}", response_model=InstitutionResponse)
def delete_institution(
    *,
    db: Session = Depends(deps.get_db),
    id: int,
    current_user: User = Depends(deps.get_current_active_superuser),
) -> Any:
    institution = institution_service.get_institution(
        db=db,
        institution_id=id,
    )
    if not institution:
        raise HTTPException(status_code=404, detail="Institution not found")
    return institution_service.delete_institution(
        db=db,
        db_obj=institution,
    )
