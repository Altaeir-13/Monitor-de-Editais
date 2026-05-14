from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class CrawlerRun(Base):
    __tablename__ = "crawler_runs"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("monitored_sources.id"), nullable=False, index=True)
    status = Column(String, nullable=False)
    items_found = Column(Integer, default=0)
    new_items = Column(Integer, default=0)
    error_message = Column(String, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=False)
    finished_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    source = relationship("MonitoredSource", back_populates="crawler_runs")
