from datetime import datetime, timezone
import enum
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from backend.app.models.base import BaseModel

class MeetingStatus(str, enum.Enum):
    UPLOADED = "UPLOADED"
    TRANSCRIBING = "TRANSCRIBING"
    TRANSCRIBED = "TRANSCRIBED"
    EXTRACTING = "EXTRACTING"
    EXTRACTED = "EXTRACTED"
    INDEXING = "INDEXING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class MeetingSourceType(str, enum.Enum):
    AUDIO = "audio"
    TRANSCRIPT = "transcript"

class Meeting(BaseModel):
    __tablename__ = "meetings"

    workspace_id = Column(String(36), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    meeting_date = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    duration_seconds = Column(Integer, default=0, nullable=False)
    source_type = Column(String(50), default=MeetingSourceType.TRANSCRIPT.value, nullable=False)
    
    # State machine tracking
    status = Column(String(50), default=MeetingStatus.UPLOADED.value, nullable=False, index=True)
    processing_stage = Column(String(100), default="Initialized", nullable=False)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    
    # Storage & Metrics
    audio_url = Column(String(500), nullable=True)
    token_count = Column(Integer, default=0, nullable=False)
    cost_usd = Column(Float, default=0.0, nullable=False)
    
    # Synthesis results
    summary = Column(Text, nullable=True)

    # Relationships
    workspace = relationship("Workspace", back_populates="meetings")
    transcript = relationship("Transcript", back_populates="meeting", uselist=False, cascade="all, delete-orphan")
    segments = relationship("TranscriptSegment", back_populates="meeting", cascade="all, delete-orphan", order_by="TranscriptSegment.segment_index")
    attendees = relationship("Attendee", back_populates="meeting", cascade="all, delete-orphan")
    decisions = relationship("Decision", back_populates="meeting", cascade="all, delete-orphan")
    action_items = relationship("ActionItem", back_populates="meeting", cascade="all, delete-orphan")
    open_questions = relationship("OpenQuestion", back_populates="meeting", cascade="all, delete-orphan")
    processing_jobs = relationship("ProcessingJob", back_populates="meeting", cascade="all, delete-orphan")
