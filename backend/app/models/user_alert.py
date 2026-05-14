from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class UserAlert(Base):
    __tablename__ = "user_alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    keyword = Column(String, nullable=False)
    institution_id = Column(Integer, ForeignKey("institutions.id"), nullable=True, index=True)
    notice_type = Column(String, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    user = relationship("User", back_populates="alerts")
    institution = relationship("Institution", back_populates="user_alerts")
