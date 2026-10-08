import os
import uuid
from typing import List, Optional
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    UploadFile,
    File,
    Form,
    Request,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.core.logging import logger
from backend.app.core.rate_limit import check_rate_limit
from backend.app.api.dependencies import get_current_user, get_current_workspace
from backend.app.models.user import User
from backend.app.models.workspace import Workspace
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

# Known audio format magic byte signatures
AUDIO_MAGIC_SIGNATURES = {
    ".mp3": [b"ID3", b"\xff\xfb", b"\xff\xf3", b"\xff\xf2"],
    ".wav": [b"RIFF"],
    ".ogg": [b"OggS"],
    ".flac": [b"fLaC"],
    ".m4a": [b"ftyp"],
}

def validate_audio_file_header(header_bytes: bytes, ext: str) -> bool:
    """Verifies that uploaded binary content matches claimed audio extension."""
    signatures = AUDIO_MAGIC_SIGNATURES.get(ext.lower(), [])
    if not signatures:
        return True  # Fallback permissive for other formats
    return any(sig in header_bytes for sig in signatures)

@router.get("", response_model=List[MeetingOut])
async def list_meetings(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    """
    Lists meetings strictly scoped to the authenticated user's active workspace.
    """
    repo = MeetingRepository(db)
    meetings = await repo.list_meetings(
        workspace_id=workspace.id, status=status, limit=limit, offset=offset
    )

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
    request: Request,
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    check_rate_limit(request, max_requests=settings.RATE_LIMIT_REQUESTS_PER_MINUTE)
    service = MeetingService(db)
    meeting = await service.create_meeting(
        title=payload.title,
        description=payload.description,
        workspace_id=workspace.id,
        source_type=payload.source_type,
        transcript_text=payload.transcript_text,
        attendee_names=payload.attendee_names,
    )
    return MeetingDetailOut.model_validate(meeting)

@router.post("/upload-audio", response_model=MeetingDetailOut)
async def upload_audio_meeting(
    request: Request,
    title: str = Form(...),
    description: Optional[str] = Form(None),
    file: UploadFile = File(...),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    check_rate_limit(request, max_requests=30)  # Max 30 uploads per minute

    # 1. Validate file extension
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in settings.ALLOWED_AUDIO_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{ext}'. Allowed: {', '.join(settings.ALLOWED_AUDIO_EXTENSIONS)}",
        )

    # 2. Validate magic bytes (first 64 bytes)
    header = await file.read(64)
    if not validate_audio_file_header(header, ext):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File content does not match the specified audio extension header signature.",
        )
    await file.seek(0)

    # 3. Stream to disk and enforce max size limit
    unique_filename = f"{uuid.uuid4()}{ext}"
    saved_path = os.path.join(settings.UPLOAD_DIR, unique_filename)
    total_bytes = 0
    chunk_size = 1024 * 64  # 64 KB chunks

    try:
        with open(saved_path, "wb") as buffer:
            while True:
                chunk = await file.read(chunk_size)
                if not chunk:
                    break
                total_bytes += len(chunk)
                if total_bytes > settings.MAX_UPLOAD_SIZE_BYTES:
                    # Clean up and reject
                    buffer.close()
                    if os.path.exists(saved_path):
                        os.remove(saved_path)
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"File exceeds maximum allowed upload size of {settings.MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)}MB",
                    )
                buffer.write(chunk)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to save upload: {e}")
        if os.path.exists(saved_path):
            os.remove(saved_path)
        raise HTTPException(status_code=500, detail="Failed to write audio file to storage")

    service = MeetingService(db)
    meeting = await service.create_meeting(
        title=title,
        description=description,
        workspace_id=workspace.id,
        source_type="audio",
        audio_file_path=saved_path,
    )
    return MeetingDetailOut.model_validate(meeting)

@router.get("/{meeting_id}", response_model=MeetingDetailOut)
async def get_meeting(
    meeting_id: str,
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    repo = MeetingRepository(db)
    meeting = await repo.get_by_id(meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    # STRICT TENANT ISOLATION CHECK
    if meeting.workspace_id != workspace.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You do not have permission to view meetings in this workspace.",
        )

    out = MeetingDetailOut.model_validate(meeting)
    out.action_items_count = len(meeting.action_items)
    out.decisions_count = len(meeting.decisions)
    return out

@router.post("/{meeting_id}/process", response_model=MeetingDetailOut)
async def trigger_processing(
    meeting_id: str,
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    repo = MeetingRepository(db)
    meeting = await repo.get_by_id(meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    if meeting.workspace_id != workspace.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You do not have permission to process meetings in this workspace.",
        )

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
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    repo = MeetingRepository(db)
    meeting = await repo.get_by_id(meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    if meeting.workspace_id != workspace.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Access denied to meeting in another workspace.",
        )

    job = await repo.get_latest_job(meeting_id)
    if not job:
        raise HTTPException(status_code=404, detail="No processing job found for this meeting")
    return ProcessingJobOut.model_validate(job)

@router.delete("/{meeting_id}")
async def delete_meeting(
    meeting_id: str,
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    repo = MeetingRepository(db)
    meeting = await repo.get_by_id(meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    if meeting.workspace_id != workspace.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Cannot delete meetings belonging to another workspace.",
        )

    deleted = await repo.delete_meeting(meeting_id)
    return {"status": "success", "message": "Meeting deleted"}
