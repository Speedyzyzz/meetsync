import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.models.meeting import Meeting, MeetingStatus, MeetingSourceType
from backend.app.models.transcript import Transcript, TranscriptSegment
from backend.app.models.attendee import Attendee
from backend.app.models.decision import Decision
from backend.app.models.action_item import ActionItem, ActionItemPriority, ActionItemStatus
from backend.app.models.open_question import OpenQuestion
from backend.app.models.processing_job import ProcessingJob
from backend.app.models.workspace import Workspace
from backend.app.repositories.meeting_repository import MeetingRepository
from backend.app.ai.transcriber import transcription_service, parse_pasted_transcript_text
from backend.app.ai.extractor import extractor

class MeetingService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = MeetingRepository(db)

    async def ensure_default_workspace(self) -> str:
        """Ensures at least one default workspace exists in the database."""
        from sqlalchemy import select
        stmt = select(Workspace).where(Workspace.id == settings.DEFAULT_WORKSPACE_ID)
        res = await self.db.execute(stmt)
        ws = res.scalar_one_or_none()
        if not ws:
            ws = Workspace(
                id=settings.DEFAULT_WORKSPACE_ID,
                name="Engineering & Product",
                slug="engineering-product",
            )
            self.db.add(ws)
            await self.db.flush()
        return ws.id

    async def create_meeting(
        self,
        title: str,
        description: Optional[str] = None,
        workspace_id: Optional[str] = None,
        source_type: str = "transcript",
        transcript_text: Optional[str] = None,
        audio_file_path: Optional[str] = None,
        attendee_names: Optional[List[str]] = None,
    ) -> Meeting:
        ws_id = workspace_id or await self.ensure_default_workspace()

        meeting = Meeting(
            workspace_id=ws_id,
            title=title,
            description=description,
            source_type=source_type,
            status=MeetingStatus.UPLOADED.value,
            processing_stage="Meeting created",
            audio_url=audio_file_path,
        )
        await self.repo.create_meeting(meeting)

        # Create attendees if provided
        if attendee_names:
            for name in attendee_names:
                att = Attendee(meeting_id=meeting.id, display_name=name)
                self.db.add(att)

        # Create processing job record
        job = ProcessingJob(
            meeting_id=meeting.id,
            status=MeetingStatus.UPLOADED.value,
            current_step="Meeting created and queued for processing",
            progress_percent=10,
        )
        await self.repo.create_job(job)
        await self.db.commit()

        # If transcript text is immediately provided, process it
        if transcript_text:
            await self.process_meeting(meeting.id, raw_transcript=transcript_text)
        elif audio_file_path:
            await self.process_meeting(meeting.id, audio_file_path=audio_file_path)

        # Refresh meeting
        refreshed = await self.repo.get_by_id(meeting.id)
        return refreshed or meeting

    async def process_meeting(
        self,
        meeting_id: str,
        raw_transcript: Optional[str] = None,
        audio_file_path: Optional[str] = None,
    ) -> Meeting:
        """
        Executes the explicit processing state machine:
        UPLOADED -> TRANSCRIBING -> TRANSCRIBED -> EXTRACTING -> EXTRACTED -> INDEXING -> COMPLETED
        Handles failures gracefully with FAILED status and error tracking.
        """
        meeting = await self.repo.get_by_id(meeting_id)
        if not meeting:
            raise ValueError(f"Meeting not found: {meeting_id}")

        job = await self.repo.get_latest_job(meeting_id)
        if not job:
            job = ProcessingJob(meeting_id=meeting.id)
            self.db.add(job)

        try:
            # 1. TRANSCRIBING STAGE
            meeting.status = MeetingStatus.TRANSCRIBING.value
            meeting.processing_stage = "Converting audio or formatting transcript into timestamped segments"
            job.status = MeetingStatus.TRANSCRIBING.value
            job.current_step = meeting.processing_stage
            job.progress_percent = 25
            await self.db.commit()

            segments_data: List[Dict[str, Any]] = []
            full_content = ""

            if audio_file_path or meeting.audio_url:
                target_audio = audio_file_path or meeting.audio_url
                segments_data = await transcription_service.transcribe_audio_file(target_audio)
                full_content = "\n".join(
                    f"{s.get('speaker', 'Speaker')}: {s.get('text', '')}" for s in segments_data
                )
            elif raw_transcript:
                full_content = raw_transcript
                segments_data = parse_pasted_transcript_text(raw_transcript)
            else:
                raise ValueError("No transcript or audio source available for processing")

            # 2. TRANSCRIBED STAGE - Persist Transcript & Segments
            meeting.status = MeetingStatus.TRANSCRIBED.value
            meeting.processing_stage = f"Transcribed {len(segments_data)} segments successfully"
            job.status = MeetingStatus.TRANSCRIBED.value
            job.current_step = meeting.processing_stage
            job.progress_percent = 45

            # Save or update transcript
            transcript_obj = meeting.transcript
            if transcript_obj:
                transcript_obj.content = full_content
            else:
                transcript_obj = Transcript(
                    meeting_id=meeting.id,
                    content=full_content,
                    language="en",
                )
                self.db.add(transcript_obj)
                await self.db.flush()

            # Clear existing segments if re-running
            for existing_seg in list(meeting.segments or []):
                await self.db.delete(existing_seg)

            for seg in segments_data:
                db_seg = TranscriptSegment(
                    transcript_id=transcript_obj.id,
                    meeting_id=meeting.id,
                    segment_index=seg["segment_index"],
                    speaker=seg.get("speaker", "Speaker"),
                    start_time=seg.get("start_time", 0.0),
                    end_time=seg.get("end_time", 0.0),
                    text=seg.get("text", ""),
                )
                self.db.add(db_seg)

            await self.db.commit()

            # 3. EXTRACTING STAGE - Structured LLM Pipeline
            meeting.status = MeetingStatus.EXTRACTING.value
            meeting.processing_stage = "Running structured LLM extraction for decisions, actions, and questions"
            job.status = MeetingStatus.EXTRACTING.value
            job.current_step = meeting.processing_stage
            job.progress_percent = 70
            await self.db.commit()

            extraction_result, tokens, cost = await extractor.extract_meeting(
                segments=segments_data,
                meeting_title=meeting.title,
            )

            # 4. EXTRACTED STAGE - Persist domain entities
            meeting.status = MeetingStatus.EXTRACTED.value
            meeting.processing_stage = "Validating extracted intelligence against Pydantic domain models"
            job.status = MeetingStatus.EXTRACTED.value
            job.current_step = meeting.processing_stage
            job.progress_percent = 85

            meeting.summary = extraction_result.summary
            meeting.token_count = tokens
            meeting.cost_usd = cost
            if extraction_result.estimated_duration_seconds:
                meeting.duration_seconds = extraction_result.estimated_duration_seconds
            elif segments_data:
                meeting.duration_seconds = int(segments_data[-1].get("end_time", 0.0))

            # Save Decisions
            for d in extraction_result.decisions:
                decision_obj = Decision(
                    meeting_id=meeting.id,
                    decision=d.decision,
                    context=d.context,
                )
                decision_obj.source_segment_ids = d.source_segment_ids
                self.db.add(decision_obj)

            # Save Action Items
            for a in extraction_result.action_items:
                act = ActionItem(
                    meeting_id=meeting.id,
                    task=a.task,
                    owner_name=a.owner,
                    priority=a.priority,
                    status=ActionItemStatus.PENDING.value,
                )
                act.source_segment_ids = a.source_segment_ids
                self.db.add(act)

            # Save Open Questions
            for q in extraction_result.open_questions:
                question_obj = OpenQuestion(
                    meeting_id=meeting.id,
                    question=q.question,
                    context=q.context,
                )
                question_obj.source_segment_ids = q.source_segment_ids
                self.db.add(question_obj)

            # 5. INDEXING & COMPLETED STAGE
            meeting.status = MeetingStatus.INDEXING.value
            meeting.processing_stage = "Finalizing indices and attendee associations"
            job.status = MeetingStatus.INDEXING.value
            job.current_step = meeting.processing_stage
            job.progress_percent = 95
            await self.db.flush()

            # Ensure detected attendees are registered
            existing_attendee_names = {att.display_name.lower() for att in meeting.attendees}
            for att_name in extraction_result.detected_attendees:
                if att_name.lower() not in existing_attendee_names:
                    self.db.add(Attendee(meeting_id=meeting.id, display_name=att_name))

            # Finalize completion
            meeting.status = MeetingStatus.COMPLETED.value
            meeting.processing_stage = "Processing completed successfully"
            job.status = MeetingStatus.COMPLETED.value
            job.current_step = "Processing completed successfully"
            job.progress_percent = 100
            job.completed_at = datetime.now(timezone.utc)

            await self.db.commit()
            logger.info(f"Meeting '{meeting.title}' ({meeting.id}) successfully processed. Tokens: {tokens}, Cost: ${cost:.4f}")

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Processing failed for meeting {meeting_id}: {str(e)}", exc_info=True)
            
            # Safely reload entity for updating failure state
            m_fail = await self.repo.get_by_id(meeting_id)
            if m_fail:
                m_fail.status = MeetingStatus.FAILED.value
                m_fail.processing_stage = "Processing failed"
                m_fail.error_message = str(e)
                m_fail.retry_count = (m_fail.retry_count or 0) + 1

            job_fail = await self.repo.get_latest_job(meeting_id)
            if job_fail:
                job_fail.status = MeetingStatus.FAILED.value
                job_fail.current_step = f"Error: {str(e)}"
                job_fail.error_message = str(e)
                job_fail.retry_count = (job_fail.retry_count or 0) + 1
                job_fail.completed_at = datetime.now(timezone.utc)

            await self.db.commit()

        refreshed = await self.repo.get_by_id(meeting_id)
        return refreshed or meeting
