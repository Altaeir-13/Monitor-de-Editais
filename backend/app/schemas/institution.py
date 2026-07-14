from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel


class InstitutionBase(BaseModel):
    name: str
    initials: str
    state: str
    official_site_url: Optional[str] = None
    logo_url: Optional[str] = None
    is_active: bool = True
    official_code: Optional[str] = None
    official_name: Optional[str] = None
    official_initials: Optional[str] = None
    region: Optional[str] = None
    headquarters_city: Optional[str] = None
    municipality_code: Optional[str] = None
    administrative_category_code: Optional[int] = None
    administrative_category: Optional[str] = None
    academic_organization_code: Optional[int] = None
    academic_organization: Optional[str] = None
    census_situation: Optional[str] = None
    current_situation: Optional[str] = None
    eligibility_status: Optional[str] = None
    eligibility_reason: Optional[str] = None
    inventory_source_url: Optional[str] = None
    inventory_reference_date: Optional[date] = None
    source_discovery_status: Optional[str] = None
    source_discovery_notes: Optional[str] = None


class InstitutionCreate(InstitutionBase):
    pass


class InstitutionUpdate(BaseModel):
    name: Optional[str] = None
    initials: Optional[str] = None
    state: Optional[str] = None
    official_site_url: Optional[str] = None
    logo_url: Optional[str] = None
    is_active: Optional[bool] = None
    official_code: Optional[str] = None
    official_name: Optional[str] = None
    official_initials: Optional[str] = None
    region: Optional[str] = None
    headquarters_city: Optional[str] = None
    municipality_code: Optional[str] = None
    administrative_category_code: Optional[int] = None
    administrative_category: Optional[str] = None
    academic_organization_code: Optional[int] = None
    academic_organization: Optional[str] = None
    census_situation: Optional[str] = None
    current_situation: Optional[str] = None
    eligibility_status: Optional[str] = None
    eligibility_reason: Optional[str] = None
    inventory_source_url: Optional[str] = None
    inventory_reference_date: Optional[date] = None
    source_discovery_status: Optional[str] = None
    source_discovery_notes: Optional[str] = None


class InstitutionInDBBase(InstitutionBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class InstitutionResponse(InstitutionInDBBase):
    pass
