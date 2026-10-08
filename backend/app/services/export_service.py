import json
from typing import Dict, Any, List
from backend.app.models.meeting import Meeting
from backend.app.schemas.export import ExportFormat, ExportResponse, JiraIssue

class ExportService:
    @staticmethod
    def export_markdown(meeting: Meeting) -> str:
        date_str = meeting.meeting_date.strftime("%B %d, %Y") if meeting.meeting_date else "Unknown Date"
        duration_mins = max(1, meeting.duration_seconds // 60)
        attendees_str = ", ".join(a.display_name for a in meeting.attendees) if meeting.attendees else "Not recorded"

        md_lines = [
            f"# {meeting.title}",
            f"**Date:** {date_str} | **Duration:** {duration_mins} mins | **Attendees:** {attendees_str}",
            "",
            "## Executive Summary",
            meeting.summary or "No summary available.",
            "",
            "## Key Decisions",
        ]

        if meeting.decisions:
            for d in meeting.decisions:
                context_str = f" *({d.context})*" if d.context else ""
                md_lines.append(f"- **{d.decision}**{context_str}")
        else:
            md_lines.append("_No decisions recorded._")

        md_lines.extend(["", "## Action Items"])
        if meeting.action_items:
            for a in meeting.action_items:
                check = "x" if a.status == "completed" else " "
                owner = f" — **{a.owner_name}**" if a.owner_name else ""
                deadline = f" (Due: {a.deadline.strftime('%b %d') if a.deadline else 'Unspecified'})"
                priority = f" `[{a.priority.upper()}]`"
                md_lines.append(f"- [{check}]{priority} {a.task}{owner}{deadline}")
        else:
            md_lines.append("_No action items recorded._")

        md_lines.extend(["", "## Open Questions"])
        if meeting.open_questions:
            for q in meeting.open_questions:
                status_mark = "✓" if q.resolved else "•"
                md_lines.append(f"{status_mark} {q.question}")
        else:
            md_lines.append("_No open questions recorded._")

        return "\n".join(md_lines)

    @staticmethod
    def export_jira_issues(meeting: Meeting) -> List[Dict[str, Any]]:
        """Converts meeting action items to Jira-compatible bulk issue import payload."""
        issues = []
        for action in meeting.action_items:
            jira_issue = {
                "fields": {
                    "project": {"key": "MEET"},
                    "summary": action.task,
                    "description": f"Extracted from meeting '{meeting.title}'.\nSource Context: Priority {action.priority.upper()}.",
                    "issuetype": {"name": "Task"},
                    "priority": {"name": action.priority.capitalize()},
                    "labels": ["meetsync", "action-item", f"meeting-{meeting.id[:8]}"],
                }
            }
            if action.owner_name:
                jira_issue["fields"]["assignee"] = {"name": action.owner_name}
            issues.append(jira_issue)
        return issues

    @classmethod
    def export_meeting(cls, meeting: Meeting, export_format: str) -> ExportResponse:
        fmt = export_format.lower()
        if fmt == ExportFormat.MARKDOWN.value:
            content = cls.export_markdown(meeting)
            return ExportResponse(
                meeting_id=meeting.id,
                meeting_title=meeting.title,
                format="markdown",
                content=content,
            )
        elif fmt == ExportFormat.JIRA.value:
            issues = cls.export_jira_issues(meeting)
            return ExportResponse(
                meeting_id=meeting.id,
                meeting_title=meeting.title,
                format="jira",
                content=json.dumps({"issueUpdates": issues}, indent=2),
                metadata={"issue_count": len(issues)},
            )
        else:  # JSON format
            data = {
                "id": meeting.id,
                "title": meeting.title,
                "meeting_date": meeting.meeting_date.isoformat(),
                "duration_seconds": meeting.duration_seconds,
                "summary": meeting.summary,
                "decisions": [{"decision": d.decision, "context": d.context} for d in meeting.decisions],
                "action_items": [
                    {
                        "task": a.task,
                        "owner": a.owner_name,
                        "priority": a.priority,
                        "status": a.status,
                    }
                    for a in meeting.action_items
                ],
                "open_questions": [{"question": q.question, "resolved": q.resolved} for q in meeting.open_questions],
            }
            return ExportResponse(
                meeting_id=meeting.id,
                meeting_title=meeting.title,
                format="json",
                content=json.dumps(data, indent=2),
            )

export_service = ExportService()
