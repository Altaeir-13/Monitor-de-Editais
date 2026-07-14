from typing import Dict, List, Literal, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.schemas.coverage import (
    CoverageBreakdownItem,
    CoverageInstitutionList,
    CoverageResponse,
)
from app.services.coverage import (
    build_coverage_report,
    list_coverage_institutions,
)
from app.services.national_seed import seed_national_catalog


RegionName = Literal[
    "Norte",
    "Nordeste",
    "Centro-Oeste",
    "Sudeste",
    "Sul",
]

CoverageStatus = Literal[
    "verified",
    "partial",
    "source_not_found",
    "temporarily_unavailable",
    "manual_review",
    "unsupported",
    "inactive",
]

router = APIRouter()


@router.get("/coverage", response_model=CoverageResponse)
def get_coverage(
    region: Optional[str] = Query(default=None, min_length=1),
    state: Optional[str] = Query(default=None, min_length=2, max_length=2),
    administrative_category_code: Optional[int] = Query(default=None),
    source_status: Optional[CoverageStatus] = Query(default=None),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
) -> CoverageResponse:
    return build_coverage_report(
        db,
        region=region,
        state=state,
        administrative_category_code=administrative_category_code,
        source_status=source_status,
    )


@router.get("/coverage/regions", response_model=List[CoverageBreakdownItem])
def get_coverage_regions(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
) -> List[CoverageBreakdownItem]:
    return build_coverage_report(db).breakdown.regions


@router.get("/coverage/institutions", response_model=CoverageInstitutionList)
def get_coverage_institutions(
    region: Optional[str] = Query(default=None, min_length=1),
    state: Optional[str] = Query(default=None, min_length=2, max_length=2),
    administrative_category_code: Optional[int] = Query(default=None),
    academic_organization_code: Optional[int] = Query(default=None),
    eligibility_status: Optional[str] = Query(default=None, min_length=1),
    coverage_status: Optional[CoverageStatus] = Query(default=None),
    verification_status: Optional[CoverageStatus] = Query(default=None),
    institution_active: Optional[bool] = Query(default=None),
    source_active: Optional[bool] = Query(default=None),
    has_source: Optional[bool] = Query(default=None),
    manual_review: Optional[bool] = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
) -> CoverageInstitutionList:
    return list_coverage_institutions(
        db,
        region=region,
        state=state,
        administrative_category_code=administrative_category_code,
        academic_organization_code=academic_organization_code,
        eligibility_status=eligibility_status,
        coverage_status=coverage_status,
        verification_status=verification_status,
        institution_active=institution_active,
        source_active=source_active,
        has_source=has_source,
        manual_review=manual_review,
        skip=skip,
        limit=limit,
    )


@router.post("/seed-national", response_model=Dict[str, int])
def trigger_seed_national(
    region: Optional[List[RegionName]] = Query(default=None),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
) -> Dict[str, int]:
    return seed_national_catalog(db=db, regions=region)
