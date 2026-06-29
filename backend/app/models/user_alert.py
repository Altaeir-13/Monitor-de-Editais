from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, text
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
    created_at = Column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=text("CURRENT_TIMESTAMP"), nullable=True)

    user = relationship("User", back_populates="alerts")
    institution = relationship("Institution", back_populates="user_alerts")
