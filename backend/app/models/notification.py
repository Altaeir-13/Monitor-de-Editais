from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint, text
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    notice_id = Column(Integer, ForeignKey("notices.id"), nullable=False, index=True)
    status = Column(String, nullable=False, default="pending")
    sent_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=text("CURRENT_TIMESTAMP"), nullable=True)

    __table_args__ = (
        UniqueConstraint('user_id', 'notice_id', name='uq_notification_user_notice'),
    )

    user = relationship("User", back_populates="notifications")
    notice = relationship("Notice", back_populates="notifications")
