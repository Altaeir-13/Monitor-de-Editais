from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class Institution(Base):
    __tablename__ = "institutions"
    __table_args__ = (
        UniqueConstraint("official_code", name="uq_institutions_official_code"),
    )

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    initials = Column(String, nullable=False, index=True)
    state = Column(String, nullable=False, index=True)
    official_site_url = Column(String, nullable=True)
    logo_url = Column(String, nullable=True)

    official_code = Column(String(32), nullable=True, index=True)
    official_name = Column(String, nullable=True)
    official_initials = Column(String, nullable=True)
    region = Column(String(16), nullable=True, index=True)
    headquarters_city = Column(String, nullable=True)
    municipality_code = Column(String(16), nullable=True)
    administrative_category_code = Column(Integer, nullable=True, index=True)
    administrative_category = Column(String, nullable=True)
    academic_organization_code = Column(Integer, nullable=True, index=True)
    academic_organization = Column(String, nullable=True)
    census_situation = Column(String(64), nullable=True)
    current_situation = Column(String(64), nullable=True)
    eligibility_status = Column(String(32), nullable=True, index=True)
    eligibility_reason = Column(Text, nullable=True)
    inventory_source_url = Column(String, nullable=True)
    inventory_reference_date = Column(Date, nullable=True)
    source_discovery_status = Column(String(32), nullable=True, index=True)
    source_discovery_notes = Column(Text, nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        onupdate=text("CURRENT_TIMESTAMP"),
        nullable=True,
    )

    monitored_sources = relationship(
        "MonitoredSource",
        back_populates="institution",
        cascade="all, delete-orphan",
    )
    notices = relationship(
        "Notice",
        back_populates="institution",
        cascade="all, delete-orphan",
    )
    user_alerts = relationship(
        "UserAlert",
        back_populates="institution",
        cascade="all, delete-orphan",
    )
