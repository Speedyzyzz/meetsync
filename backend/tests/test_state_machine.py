import pytest
from backend.app.services.meeting_service import MeetingService
from backend.app.models.meeting import MeetingStatus

@pytest.mark.asyncio
async def test_processing_state_machine_happy_path(test_session):
    service = MeetingService(test_session)
    ws_id = await service.ensure_default_workspace()
    
    raw_transcript = (
        "00:00:10 Arun: Let's move the launch to Friday.\n"
        "00:00:25 Ravi: Agreed. I will finish QA testing by Thursday."
    )
    
    meeting = await service.create_meeting(
        title="Sprint Sync",
        workspace_id=ws_id,
        source_type="transcript",
        transcript_text=raw_transcript,
    )
    
    assert meeting.status == MeetingStatus.COMPLETED.value
    assert meeting.summary is not None
    assert len(meeting.segments) == 2
    assert len(meeting.decisions) >= 1
    assert len(meeting.action_items) >= 1

@pytest.mark.asyncio
async def test_processing_state_machine_failure_handling(test_session):
    service = MeetingService(test_session)
    ws_id = await service.ensure_default_workspace()
    
    # Meeting with no transcript or audio
    meeting = await service.create_meeting(
        title="Empty Meeting",
        workspace_id=ws_id,
        source_type="transcript",
    )
    
    # Trigger processing with missing content should fail gracefully
    processed = await service.process_meeting(meeting.id, raw_transcript=None, audio_file_path=None)
    assert processed.status == MeetingStatus.FAILED.value
    assert "No transcript or audio source" in (processed.error_message or "")
    assert processed.retry_count == 1
