from typing import List, Literal, Optional
from pydantic import BaseModel, Field

class ActionItemExtraction(BaseModel):
    task: str = Field(description="Clear, actionable task description")
    owner: Optional[str] = Field(default=None, description="Name of the person assigned, or null if unassigned")
    deadline: Optional[str] = Field(default=None, description="Due date or time frame (e.g. 'Oct 9', '2026-10-15', 'End of sprint')")
    priority: Literal["low", "medium", "high"] = Field(default="medium", description="Priority level of the task")
    source_segment_ids: List[int] = Field(default_factory=list, description="IDs of transcript segments proving or mentioning this action")

class DecisionExtraction(BaseModel):
    decision: str = Field(description="Explicit decision agreed upon by the team")
    context: Optional[str] = Field(default=None, description="Brief rationale or surrounding context for why this was decided")
    source_segment_ids: List[int] = Field(default_factory=list, description="IDs of transcript segments mentioning this decision")

class OpenQuestionExtraction(BaseModel):
    question: str = Field(description="Unresolved question or open dilemma raised during the meeting")
    context: Optional[str] = Field(default=None, description="Context regarding who needs to answer or investigate")
    source_segment_ids: List[int] = Field(default_factory=list, description="IDs of transcript segments where question was raised")

class MeetingExtraction(BaseModel):
    summary: str = Field(description="Executive summary synthesizing the primary topics, outcomes, and progress")
    decisions: List[DecisionExtraction] = Field(default_factory=list, description="List of decisions reached")
    action_items: List[ActionItemExtraction] = Field(default_factory=list, description="List of concrete action items")
    open_questions: List[OpenQuestionExtraction] = Field(default_factory=list, description="List of unresolved open questions")
    detected_attendees: List[str] = Field(default_factory=list, description="Names of individuals participating or mentioned")
    estimated_duration_seconds: Optional[int] = Field(default=None, description="Estimated meeting duration in seconds if discernible")
