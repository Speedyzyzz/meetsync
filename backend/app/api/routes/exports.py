from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.database import get_db
from backend.app.repositories.meeting_repository import MeetingRepository
from backend.app.services.export_service import export_service
from backend.app.schemas.export import ExportResponse

router = APIRouter()

@router.get("/{meeting_id}/export", response_model=ExportResponse)
async def export_meeting(
    meeting_id: str,
    format: str = Query("markdown", pattern="^(markdown|json|jira)$"),
    db: AsyncSession = Depends(get_db),
):
    repo = MeetingRepository(db)
    meeting = await repo.get_by_id(meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    return export_service.export_meeting(meeting, export_format=format)
