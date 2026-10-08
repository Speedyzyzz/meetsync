from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from backend.app.models.base import BaseModel

class ProcessingJob(BaseModel):
    __tablename__ = "processing_jobs"

    meeting_id = Column(String(36), ForeignKey("meetings.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(50), default="UPLOADED", nullable=False, index=True)
    current_step = Column(String(255), default="Job created", nullable=False)
    progress_percent = Column(Integer, default=0, nullable=False)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    completed_at = Column(DateTime, nullable=True)

    meeting = relationship("Meeting", back_populates="processing_jobs")
