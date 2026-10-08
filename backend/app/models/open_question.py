import json
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from backend.app.models.base import BaseModel

class OpenQuestion(BaseModel):
    __tablename__ = "open_questions"

    meeting_id = Column(String(36), ForeignKey("meetings.id", ondelete="CASCADE"), nullable=False, index=True)
    question = Column(Text, nullable=False)
    context = Column(Text, nullable=True)
    resolved = Column(Boolean, default=False, nullable=False)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(String(255), nullable=True)
    _source_segment_ids = Column("source_segment_ids", Text, default="[]", nullable=False)

    meeting = relationship("Meeting", back_populates="open_questions")

    @property
    def source_segment_ids(self) -> List[int]:
        try:
            return json.loads(self._source_segment_ids or "[]")
        except Exception:
            return []

    @source_segment_ids.setter
    def source_segment_ids(self, values: List[int]) -> None:
        self._source_segment_ids = json.dumps(values if values else [])

    def mark_resolved(self, resolved_by_name: str) -> None:
        self.resolved = True
        self.resolved_at = datetime.now(timezone.utc)
        self.resolved_by = resolved_by_name
