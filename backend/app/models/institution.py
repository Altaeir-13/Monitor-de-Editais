from sqlalchemy import Column, Integer, String, Boolean, DateTime, text
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class Institution(Base):
    __tablename__ = "institutions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    initials = Column(String, nullable=False, index=True)
    state = Column(String, nullable=False, index=True)
    official_site_url = Column(String, nullable=False)
    logo_url = Column(String, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=text("CURRENT_TIMESTAMP"), nullable=True)

    monitored_sources = relationship("MonitoredSource", back_populates="institution", cascade="all, delete-orphan")
    notices = relationship("Notice", back_populates="institution", cascade="all, delete-orphan")
    user_alerts = relationship("UserAlert", back_populates="institution", cascade="all, delete-orphan")
