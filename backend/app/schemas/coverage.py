from typing import Dict, List, Optional

from pydantic import BaseModel


class InventoryCoverage(BaseModel):
    census_raw_total: int
    eligible_census_total: int
    post_census_total: int
    inventory_total: int
    eligible_total: int
    registered: int
    percent: float


class CoverageStage(BaseModel):
    institutions: int
    percent: float


class CoverageBreakdownItem(BaseModel):
    key: str
    label: str
    inventory_total: int
    eligible_total: int
    mapped_sources: int
    institutions_with_source: int
    institutions_without_source: int
    verified: int
    partial: int
    manual_review: int
    source_not_found: int
    capture_validated: int
    active_monitoring: int


class SpiderBreakdownItem(BaseModel):
    spider: str
    sources: int
    institutions: int


class CoverageBreakdown(BaseModel):
    regions: List[CoverageBreakdownItem]
    states: List[CoverageBreakdownItem]
    administrative_categories: List[CoverageBreakdownItem]
    academic_organizations: List[CoverageBreakdownItem]
    spiders: List[SpiderBreakdownItem]


class CoveragePendingItem(BaseModel):
    official_code: str
    official_name: str
    state: str
    region: str
    status: str
    reason: str


class CoverageInstitutionItem(BaseModel):
    official_code: str
    official_name: str
    initials: str
    state: str
    region: str
    administrative_category_code: Optional[int] = None
    administrative_category: Optional[str] = None
    academic_organization_code: Optional[int] = None
    academic_organization: Optional[str] = None
    eligibility_status: str
    eligibility_reason: Optional[str] = None
    coverage_status: str
    coverage_notes: Optional[str] = None
    source_count: int
    source_statuses: List[str]
    has_source: bool
    registered: bool
    institution_active: Optional[bool] = None
    source_active: bool
    capture_validated: bool
    active_monitoring: bool


class CoverageInstitutionList(BaseModel):
    total: int
    skip: int
    limit: int
    items: List[CoverageInstitutionItem]


class CoverageResponse(BaseModel):
    inventory_total: int
    eligible_target_total: int
    mapped_source_total_inventory: int
    mapped_source_total_eligible: int
    institutions_with_source: int
    institutions_without_source: int
    verified_source_institutions: int
    partial_source_institutions: int
    manual_review_institutions: int
    source_not_found_institutions: int
    validated_capture_total: int
    active_monitoring_total: int
    inventory: InventoryCoverage
    mapped: CoverageStage
    verified: CoverageStage
    capture_validated: CoverageStage
    active_monitoring: CoverageStage
    institution_status_counts: Dict[str, int]
    source_status_counts: Dict[str, int]
    breakdown: CoverageBreakdown
    last_audit: Optional[str] = None
    pending: List[CoveragePendingItem]
