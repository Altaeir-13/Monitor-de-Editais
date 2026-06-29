from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, text
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class Notice(Base):
    __tablename__ = "notices"

    id = Column(Integer, primary_key=True, index=True)
    institution_id = Column(Integer, ForeignKey("institutions.id"), nullable=False, index=True)
    source_id = Column(Integer, ForeignKey("monitored_sources.id"), nullable=False, index=True)
    title = Column(String, nullable=False)
    normalized_title = Column(String, nullable=False)
    url = Column(String, nullable=False)
    normalized_url = Column(String, nullable=False)
    notice_type = Column(String, nullable=False, index=True)
    publication_date = Column(DateTime(timezone=True), nullable=True)
    detected_at = Column(DateTime(timezone=True), nullable=False, index=True, default=text("CURRENT_TIMESTAMP"))
    description = Column(String, nullable=True)
    content_hash = Column(String, nullable=True)
    fingerprint = Column(String, unique=True, nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=text("CURRENT_TIMESTAMP"), nullable=True)

    institution = relationship("Institution", back_populates="notices")
    source = relationship("MonitoredSource", back_populates="notices")
    notifications = relationship("Notification", back_populates="notice", cascade="all, delete-orphan")
