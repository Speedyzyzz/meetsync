from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.action_item import ActionItem

class ActionItemRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, action_id: str) -> Optional[ActionItem]:
        stmt = select(ActionItem).where(ActionItem.id == action_id)
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def list_action_items(
        self,
        meeting_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> List[ActionItem]:
        stmt = select(ActionItem).order_by(ActionItem.created_at.desc()).limit(limit)
        if meeting_id:
            stmt = stmt.where(ActionItem.meeting_id == meeting_id)
        if status:
            stmt = stmt.where(ActionItem.status == status)

        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def update(self, action_item: ActionItem) -> ActionItem:
        await self.db.flush()
        return action_item
