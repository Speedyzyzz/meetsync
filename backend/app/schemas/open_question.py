from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict

class OpenQuestionOut(BaseModel):
    id: str
    meeting_id: str
    question: str
    context: Optional[str] = None
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    source_segment_ids: List[int] = Field(default_factory=list)
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class OpenQuestionResolve(BaseModel):
    resolved_by: str = "User"
