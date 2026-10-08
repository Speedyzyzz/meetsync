import enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

class ExportFormat(str, enum.Enum):
    MARKDOWN = "markdown"
    JSON = "json"
    JIRA = "jira"

class JiraIssue(BaseModel):
    summary: str
    description: str
    issue_type: str = "Task"
    priority: str = "Medium"
    assignee: Optional[str] = None
    due_date: Optional[str] = None
    labels: List[str] = ["meetsync", "action-item"]

class ExportResponse(BaseModel):
    meeting_id: str
    meeting_title: str
    format: str
    content: str
    metadata: Optional[Dict[str, Any]] = None
