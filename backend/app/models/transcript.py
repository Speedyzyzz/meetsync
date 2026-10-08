from sqlalchemy import Column, String, Integer, Float, ForeignKey, Text
from sqlalchemy.orm import relationship
from backend.app.models.base import BaseModel

class Transcript(BaseModel):
    __tablename__ = "transcripts"

    meeting_id = Column(String(36), ForeignKey("meetings.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    content = Column(Text, nullable=False)
    language = Column(String(10), default="en", nullable=False)

    meeting = relationship("Meeting", back_populates="transcript")
    segments = relationship("TranscriptSegment", back_populates="transcript", cascade="all, delete-orphan", order_by="TranscriptSegment.segment_index")

class TranscriptSegment(BaseModel):
    __tablename__ = "transcript_segments"

    transcript_id = Column(String(36), ForeignKey("transcripts.id", ondelete="CASCADE"), nullable=False, index=True)
    meeting_id = Column(String(36), ForeignKey("meetings.id", ondelete="CASCADE"), nullable=False, index=True)
    segment_index = Column(Integer, nullable=False, index=True)
    speaker = Column(String(100), default="Speaker", nullable=False)
    start_time = Column(Float, default=0.0, nullable=False)  # Seconds
    end_time = Column(Float, default=0.0, nullable=False)    # Seconds
    text = Column(Text, nullable=False)

    transcript = relationship("Transcript", back_populates="segments")
    meeting = relationship("Meeting", back_populates="segments")
