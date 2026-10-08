from typing import List, Optional
from sqlalchemy import select, func, or_, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from backend.app.models.meeting import Meeting, MeetingStatus
from backend.app.models.transcript import Transcript, TranscriptSegment
from backend.app.models.decision import Decision
from backend.app.models.action_item import ActionItem
from backend.app.models.open_question import OpenQuestion
from backend.app.models.attendee import Attendee
from backend.app.models.processing_job import ProcessingJob

class MeetingRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, meeting_id: str) -> Optional[Meeting]:
        stmt = (
            select(Meeting)
            .where(Meeting.id == meeting_id)
            .execution_options(populate_existing=True)
            .options(
                selectinload(Meeting.transcript),
                selectinload(Meeting.segments),
                selectinload(Meeting.attendees),
                selectinload(Meeting.decisions),
                selectinload(Meeting.action_items),
                selectinload(Meeting.open_questions),
                selectinload(Meeting.processing_jobs),
            )
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def list_meetings(
        self,
        workspace_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Meeting]:
        stmt = select(Meeting).options(
            selectinload(Meeting.action_items),
            selectinload(Meeting.decisions),
            selectinload(Meeting.attendees),
        ).order_by(Meeting.meeting_date.desc()).limit(limit).offset(offset)
        
        if workspace_id:
            stmt = stmt.where(Meeting.workspace_id == workspace_id)
        if status:
            stmt = stmt.where(Meeting.status == status)

        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def create_meeting(self, meeting: Meeting) -> Meeting:
        self.db.add(meeting)
        await self.db.flush()
        return meeting

    async def delete_meeting(self, meeting_id: str) -> bool:
        stmt = select(Meeting).where(Meeting.id == meeting_id)
        res = await self.db.execute(stmt)
        meeting = res.scalar_one_or_none()
        if not meeting:
            return False
        await self.db.delete(meeting)
        await self.db.flush()
        return True

    async def create_job(self, job: ProcessingJob) -> ProcessingJob:
        self.db.add(job)
        await self.db.flush()
        return job

    async def get_latest_job(self, meeting_id: str) -> Optional[ProcessingJob]:
        stmt = (
            select(ProcessingJob)
            .where(ProcessingJob.meeting_id == meeting_id)
            .order_by(ProcessingJob.started_at.desc())
            .limit(1)
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def search(
        self,
        query: str,
        workspace_id: Optional[str] = None,
        limit: int = 20,
    ) -> List[dict]:
        """
        Unified search querying meeting titles, summaries, decisions, and transcript segments.
        Supports SQLite (LIKE / string matching) and PostgreSQL (ILIKE or tsvector).
        """
        search_term = f"%{query}%"
        results = []

        # 1. Search transcript segments
        seg_stmt = (
            select(TranscriptSegment, Meeting)
            .join(Meeting, TranscriptSegment.meeting_id == Meeting.id)
            .where(TranscriptSegment.text.ilike(search_term))
            .limit(limit)
        )
        if workspace_id:
            seg_stmt = seg_stmt.where(Meeting.workspace_id == workspace_id)
        seg_res = await self.db.execute(seg_stmt)
        for seg, meet in seg_res.all():
            results.append({
                "meeting_id": meet.id,
                "meeting_title": meet.title,
                "result_type": "transcript",
                "snippet": seg.text,
                "matched_segment_id": seg.segment_index,
                "timestamp_seconds": seg.start_time,
                "speaker": seg.speaker,
            })

        # 2. Search meeting titles & summaries
        meet_stmt = (
            select(Meeting)
            .where(
                or_(
                    Meeting.title.ilike(search_term),
                    Meeting.summary.ilike(search_term),
                )
            )
            .limit(limit)
        )
        if workspace_id:
            meet_stmt = meet_stmt.where(Meeting.workspace_id == workspace_id)
        meet_res = await self.db.execute(meet_stmt)
        for meet in meet_res.scalars().all():
            results.append({
                "meeting_id": meet.id,
                "meeting_title": meet.title,
                "result_type": "summary",
                "snippet": meet.summary or meet.title,
                "matched_segment_id": None,
                "timestamp_seconds": None,
                "speaker": None,
            })

        # 3. Search decisions
        dec_stmt = (
            select(Decision, Meeting)
            .join(Meeting, Decision.meeting_id == Meeting.id)
            .where(Decision.decision.ilike(search_term))
            .limit(limit)
        )
        if workspace_id:
            dec_stmt = dec_stmt.where(Meeting.workspace_id == workspace_id)
        dec_res = await self.db.execute(dec_stmt)
        for dec, meet in dec_res.all():
            results.append({
                "meeting_id": meet.id,
                "meeting_title": meet.title,
                "result_type": "decision",
                "snippet": dec.decision,
                "matched_segment_id": dec.source_segment_ids[0] if dec.source_segment_ids else None,
                "timestamp_seconds": None,
                "speaker": None,
            })

        return results[:limit]
