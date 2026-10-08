from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict

class TranscriptSegmentBase(BaseModel):
    segment_index: int
    speaker: str
    start_time: float
    end_time: float
    text: str

class TranscriptSegmentCreate(TranscriptSegmentBase):
    pass

class TranscriptSegmentOut(TranscriptSegmentBase):
    id: str
    transcript_id: str
    meeting_id: str
    model_config = ConfigDict(from_attributes=True)

class TranscriptOut(BaseModel):
    id: str
    meeting_id: str
    content: str
    language: str
    segments: List[TranscriptSegmentOut] = Field(default_factory=list)
    model_config = ConfigDict(from_attributes=True)
