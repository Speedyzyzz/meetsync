from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict

class DecisionOut(BaseModel):
    id: str
    meeting_id: str
    decision: str
    context: Optional[str] = None
    source_segment_ids: List[int] = Field(default_factory=list)
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
