import json
import enum
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from backend.app.models.base import BaseModel

class ActionItemPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class ActionItemStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class ActionItem(BaseModel):
    __tablename__ = "action_items"

    meeting_id = Column(String(36), ForeignKey("meetings.id", ondelete="CASCADE"), nullable=False, index=True)
    task = Column(Text, nullable=False)
    owner_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    owner_name = Column(String(255), nullable=True)
    deadline = Column(DateTime, nullable=True)
    priority = Column(String(50), default=ActionItemPriority.MEDIUM.value, nullable=False)
    status = Column(String(50), default=ActionItemStatus.PENDING.value, nullable=False, index=True)
    _source_segment_ids = Column("source_segment_ids", Text, default="[]", nullable=False)
    completed_at = Column(DateTime, nullable=True)

    meeting = relationship("Meeting", back_populates="action_items")

    @property
    def source_segment_ids(self) -> List[int]:
        try:
            return json.loads(self._source_segment_ids or "[]")
        except Exception:
            return []

    @source_segment_ids.setter
    def source_segment_ids(self, values: List[int]) -> None:
        self._source_segment_ids = json.dumps(values if values else [])

    def mark_completed(self) -> None:
        self.status = ActionItemStatus.COMPLETED.value
        self.completed_at = datetime.now(timezone.utc)

    def mark_pending(self) -> None:
        self.status = ActionItemStatus.PENDING.value
        self.completed_at = None
