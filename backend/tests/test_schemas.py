import pytest
from pydantic import ValidationError
from backend.app.schemas.extraction import (
    MeetingExtraction,
    ActionItemExtraction,
    DecisionExtraction,
    OpenQuestionExtraction,
)

def test_action_item_valid():
    item = ActionItemExtraction(
        task="Complete database migration",
        owner="Sarah",
        deadline="Friday EOD",
        priority="high",
        source_segment_ids=[1, 2],
    )
    assert item.task == "Complete database migration"
    assert item.priority == "high"
    assert item.source_segment_ids == [1, 2]

def test_action_item_invalid_priority():
    with pytest.raises(ValidationError):
        ActionItemExtraction(
            task="Invalid priority task",
            priority="critical",  # Only low, medium, high allowed
        )

def test_decision_extraction():
    dec = DecisionExtraction(
        decision="Move product launch to Friday",
        context="Engineering needed QA buffer",
        source_segment_ids=[3],
    )
    assert dec.decision == "Move product launch to Friday"
    assert dec.source_segment_ids == [3]

def test_meeting_extraction_full():
    data = {
        "summary": "The team agreed on the launch date and assigned key tasks.",
        "decisions": [
            {"decision": "Launch Friday", "context": "QA ready", "source_segment_ids": [1]}
        ],
        "action_items": [
            {"task": "Run tests", "owner": "Ravi", "deadline": "Thursday", "priority": "high", "source_segment_ids": [2]}
        ],
        "open_questions": [
            {"question": "Who owns communications?", "context": "Customer outreach", "source_segment_ids": [3]}
        ],
        "detected_attendees": ["Arun", "Sarah", "Ravi"],
        "estimated_duration_seconds": 1200,
    }
    extracted = MeetingExtraction.model_validate(data)
    assert len(extracted.decisions) == 1
    assert len(extracted.action_items) == 1
    assert len(extracted.open_questions) == 1
    assert extracted.estimated_duration_seconds == 1200
