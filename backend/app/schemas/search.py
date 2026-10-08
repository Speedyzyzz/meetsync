from typing import List, Optional
from pydantic import BaseModel, Field

class SearchResultItem(BaseModel):
    meeting_id: str
    meeting_title: str
    result_type: str  # "transcript", "decision", "action_item", "summary"
    snippet: str
    matched_segment_id: Optional[int] = None
    timestamp_seconds: Optional[float] = None
    speaker: Optional[str] = None

class SearchResponse(BaseModel):
    query: str
    total_matches: int
    results: List[SearchResultItem] = Field(default_factory=list)
