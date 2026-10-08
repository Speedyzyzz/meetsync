import os
import uuid
import shutil
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.core.logging import logger
from backend.app.models.meeting import Meeting, MeetingStatus
from backend.app.repositories.meeting_repository import MeetingRepository
from backend.app.services.meeting_service import MeetingService
from backend.app.schemas.meeting import (
    MeetingCreate,
    MeetingOut,
    MeetingDetailOut,
    MeetingUpdate,
    ProcessingJobOut,
)

router = APIRouter()

@router.get("", response_model=List[MeetingOut])
async def list_meetings(
    workspace_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    repo = MeetingRepository(db)
    meetings = await repo.list_meetings(
        workspace_id=workspace_id, status=status, limit=limit, offset=offset
    )
    
    # Compute counts
    results = []
    for m in meetings:
        out = MeetingOut.model_validate(m)
        out.action_items_count = len(m.action_items) if m.action_items else 0
        out.decisions_count = len(m.decisions) if m.decisions else 0
        results.append(out)
    return results

@router.post("", response_model=MeetingDetailOut)
async def create_meeting(
    payload: MeetingCreate,
    db: AsyncSession = Depends(get_db),
):
    service = MeetingService(db)
    meeting = await service.create_meeting(
        title=payload.title,
        description=payload.description,
        workspace_id=payload.workspace_id,
        source_type=payload.source_type,
        transcript_text=payload.transcript_text,
        attendee_names=payload.attendee_names,
    )
    return MeetingDetailOut.model_validate(meeting)

@router.post("/upload-audio", response_model=MeetingDetailOut)
async def upload_audio_meeting(
    title: str = Form(...),
    description: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    # Validate file extension
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in settings.ALLOWED_AUDIO_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format '{ext}'. Allowed: {', '.join(settings.ALLOWED_AUDIO_EXTENSIONS)}",
        )

    # Save audio file to storage directory
    unique_filename = f"{uuid.uuid4()}{ext}"
    saved_path = os.path.join(settings.UPLOAD_DIR, unique_filename)
    try:
        with open(saved_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        logger.error(f"Failed to save upload: {e}")
        raise HTTPException(status_code=500, detail="Failed to save audio file to disk")

    service = MeetingService(db)
    meeting = await service.create_meeting(
        title=title,
        description=description,
        source_type="audio",
        audio_file_path=saved_path,
    )
    return MeetingDetailOut.model_validate(meeting)

@router.get("/{meeting_id}", response_model=MeetingDetailOut)
async def get_meeting(
    meeting_id: str,
    db: AsyncSession = Depends(get_db),
):
    repo = MeetingRepository(db)
    meeting = await repo.get_by_id(meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    out = MeetingDetailOut.model_validate(meeting)
    out.action_items_count = len(meeting.action_items)
    out.decisions_count = len(meeting.decisions)
    return out

@router.post("/{meeting_id}/process", response_model=MeetingDetailOut)
async def trigger_processing(
    meeting_id: str,
    db: AsyncSession = Depends(get_db),
):
    repo = MeetingRepository(db)
    meeting = await repo.get_by_id(meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    service = MeetingService(db)
    raw_text = meeting.transcript.content if meeting.transcript else None
    processed = await service.process_meeting(
        meeting_id=meeting.id,
        raw_transcript=raw_text,
        audio_file_path=meeting.audio_url,
    )
    return MeetingDetailOut.model_validate(processed)

@router.get("/{meeting_id}/status", response_model=ProcessingJobOut)
async def get_processing_status(
    meeting_id: str,
    db: AsyncSession = Depends(get_db),
):
    repo = MeetingRepository(db)
    job = await repo.get_latest_job(meeting_id)
    if not job:
        raise HTTPException(status_code=404, detail="No processing job found for this meeting")
    return ProcessingJobOut.model_validate(job)

@router.delete("/{meeting_id}")
async def delete_meeting(
    meeting_id: str,
    db: AsyncSession = Depends(get_db),
):
    repo = MeetingRepository(db)
    deleted = await repo.delete_meeting(meeting_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return {"status": "success", "message": "Meeting deleted"}
