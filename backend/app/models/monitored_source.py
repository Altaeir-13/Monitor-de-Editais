from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class MonitoredSource(Base):
    __tablename__ = "monitored_sources"
    __table_args__ = (
        UniqueConstraint(
            "catalog_source_id",
            name="uq_monitored_sources_catalog_source_id",
        ),
        UniqueConstraint(
            "institution_id",
            "normalized_url",
            name="uq_monitored_sources_institution_normalized_url",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    institution_id = Column(
        Integer,
        ForeignKey("institutions.id"),
        nullable=False,
        index=True,
    )
    name = Column(String, nullable=False)
    url = Column(String, nullable=False)
    source_type = Column(String, nullable=False)
    catalog_source_id = Column(String(128), nullable=True, index=True)
    normalized_url = Column(String, nullable=True, index=True)
    content_type = Column(String(64), nullable=True)
    recommended_spider = Column(String(32), nullable=True)
    coverage_status = Column(String(32), nullable=True, index=True)
    last_verified_at = Column(DateTime(timezone=True), nullable=True)
    verification_http_status = Column(Integer, nullable=True)
    verification_final_url = Column(String, nullable=True)
    verification_redirect_chain = Column(Text, nullable=True)
    verification_page_title = Column(String, nullable=True)
    verification_evidence = Column(Text, nullable=True)
    verification_notes = Column(Text, nullable=True)
    priority = Column(Integer, nullable=True)
    notice_categories = Column(Text, nullable=True)
    capture_validated_at = Column(DateTime(timezone=True), nullable=True)
    capture_evidence = Column(Text, nullable=True)
    check_frequency_minutes = Column(Integer, nullable=False, default=1440)
    last_checked_at = Column(DateTime(timezone=True), nullable=True)
    last_success_at = Column(DateTime(timezone=True), nullable=True)
    last_error_message = Column(String, nullable=True)
    is_active = Column(Boolean, default=False, nullable=False)
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

    institution = relationship("Institution", back_populates="monitored_sources")
    notices = relationship(
        "Notice",
        back_populates="source",
        cascade="all, delete-orphan",
    )
    crawler_runs = relationship(
        "CrawlerRun",
        back_populates="source",
        cascade="all, delete-orphan",
    )
