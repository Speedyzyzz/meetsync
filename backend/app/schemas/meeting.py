from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
from backend.app.schemas.transcript import TranscriptSegmentOut
from backend.app.schemas.decision import DecisionOut
from backend.app.schemas.action_item import ActionItemOut
from backend.app.schemas.open_question import OpenQuestionOut

class AttendeeOut(BaseModel):
    id: str
    meeting_id: str
    display_name: str
    email: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class MeetingCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    workspace_id: Optional[str] = None
    source_type: str = "transcript"  # "transcript" or "audio"
    transcript_text: Optional[str] = None
    attendee_names: List[str] = Field(default_factory=list)

class MeetingUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    summary: Optional[str] = None

class MeetingOut(BaseModel):
    id: str
    workspace_id: str
    title: str
    description: Optional[str] = None
    meeting_date: datetime
    duration_seconds: int
    source_type: str
    status: str
    processing_stage: str
    error_message: Optional[str] = None
    retry_count: int
    token_count: int
    cost_usd: float
    summary: Optional[str] = None
    action_items_count: int = 0
    decisions_count: int = 0
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class MeetingDetailOut(MeetingOut):
    attendees: List[AttendeeOut] = Field(default_factory=list)
    segments: List[TranscriptSegmentOut] = Field(default_factory=list)
    decisions: List[DecisionOut] = Field(default_factory=list)
    action_items: List[ActionItemOut] = Field(default_factory=list)
    open_questions: List[OpenQuestionOut] = Field(default_factory=list)
    model_config = ConfigDict(from_attributes=True)

class ProcessingJobOut(BaseModel):
    id: str
    meeting_id: str
    status: str
    current_step: str
    progress_percent: int
    error_message: Optional[str] = None
    retry_count: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)
