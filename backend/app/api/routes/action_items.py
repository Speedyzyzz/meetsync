from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.database import get_db
from backend.app.api.dependencies import get_current_workspace
from backend.app.models.workspace import Workspace
from backend.app.models.action_item import ActionItem, ActionItemStatus
from backend.app.repositories.action_item_repository import ActionItemRepository
from backend.app.schemas.action_item import ActionItemOut, ActionItemUpdate

router = APIRouter()

@router.get("", response_model=List[ActionItemOut])
async def list_action_items(
    meeting_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    repo = ActionItemRepository(db)
    items = await repo.list_action_items(
        workspace_id=workspace.id,
        meeting_id=meeting_id,
        status=status,
        limit=limit,
    )
    return [ActionItemOut.model_validate(i) for i in items]

@router.patch("/{action_id}", response_model=ActionItemOut)
async def update_action_item(
    action_id: str,
    payload: ActionItemUpdate,
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    repo = ActionItemRepository(db)
    item = await repo.get_by_id(action_id)
    if not item:
        raise HTTPException(status_code=404, detail="Action item not found")

    # STRICT TENANT ISOLATION CHECK
    if item.meeting and item.meeting.workspace_id != workspace.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Cannot modify action item belonging to another workspace.",
        )

    if payload.status is not None:
        if payload.status == ActionItemStatus.COMPLETED.value:
            item.mark_completed()
        elif payload.status == ActionItemStatus.PENDING.value:
            item.mark_pending()
        else:
            item.status = payload.status

    if payload.task is not None:
        item.task = payload.task
    if payload.owner_name is not None:
        item.owner_name = payload.owner_name
    if payload.priority is not None:
        item.priority = payload.priority
    if payload.deadline is not None:
        item.deadline = payload.deadline

    await repo.update(item)
    await db.commit()
    return ActionItemOut.model_validate(item)
