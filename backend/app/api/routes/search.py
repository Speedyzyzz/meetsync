from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.database import get_db
from backend.app.api.dependencies import get_current_workspace
from backend.app.models.workspace import Workspace
from backend.app.repositories.meeting_repository import MeetingRepository
from backend.app.schemas.search import SearchResponse, SearchResultItem

router = APIRouter()

@router.get("", response_model=SearchResponse)
async def search_meetings(
    q: str = Query(..., min_length=1, description="Search query string"),
    limit: int = Query(25, ge=1, le=100),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    """
    Executes search strictly scoped to the active authorized workspace.
    """
    repo = MeetingRepository(db)
    raw_results = await repo.search(query=q, workspace_id=workspace.id, limit=limit)
    items = [SearchResultItem(**item) for item in raw_results]
    return SearchResponse(
        query=q,
        total_matches=len(items),
        results=items,
    )
