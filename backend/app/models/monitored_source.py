from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, text
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class MonitoredSource(Base):
    __tablename__ = "monitored_sources"

    id = Column(Integer, primary_key=True, index=True)
    institution_id = Column(Integer, ForeignKey("institutions.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False)
    source_type = Column(String, nullable=False)
    check_frequency_minutes = Column(Integer, nullable=False, default=1440)
    last_checked_at = Column(DateTime(timezone=True), nullable=True)
    last_success_at = Column(DateTime(timezone=True), nullable=True)
    last_error_message = Column(String, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=text("CURRENT_TIMESTAMP"), nullable=True)

    institution = relationship("Institution", back_populates="monitored_sources")
    notices = relationship("Notice", back_populates="source", cascade="all, delete-orphan")
    crawler_runs = relationship("CrawlerRun", back_populates="source", cascade="all, delete-orphan")
