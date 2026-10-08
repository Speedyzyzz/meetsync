from datetime import datetime
from typing import List, Literal, Optional
from pydantic import BaseModel, Field, ConfigDict

class ActionItemBase(BaseModel):
    task: str
    owner_name: Optional[str] = None
    deadline: Optional[datetime] = None
    priority: Literal["low", "medium", "high"] = "medium"
    status: Literal["pending", "in_progress", "completed", "cancelled"] = "pending"

class ActionItemCreate(ActionItemBase):
    meeting_id: str
    source_segment_ids: List[int] = Field(default_factory=list)

class ActionItemUpdate(BaseModel):
    task: Optional[str] = None
    owner_name: Optional[str] = None
    deadline: Optional[datetime] = None
    priority: Optional[Literal["low", "medium", "high"]] = None
    status: Optional[Literal["pending", "in_progress", "completed", "cancelled"]] = None

class ActionItemOut(ActionItemBase):
    id: str
    meeting_id: str
    owner_id: Optional[str] = None
    source_segment_ids: List[int] = Field(default_factory=list)
    created_at: datetime
    completed_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)
