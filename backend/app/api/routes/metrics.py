from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.database import get_db
from backend.app.models.meeting import Meeting
from backend.app.models.action_item import ActionItem, ActionItemStatus
from backend.app.models.decision import Decision

router = APIRouter()

@router.get("/usage")
async def get_usage_metrics(db: AsyncSession = Depends(get_db)):
    # Total meetings
    meetings_count = await db.scalar(select(func.count(Meeting.id))) or 0
    completed_meetings = await db.scalar(select(func.count(Meeting.id)).where(Meeting.status == "COMPLETED")) or 0

    # Action items
    total_actions = await db.scalar(select(func.count(ActionItem.id))) or 0
    completed_actions = await db.scalar(select(func.count(ActionItem.id)).where(ActionItem.status == ActionItemStatus.COMPLETED.value)) or 0
    pending_actions = total_actions - completed_actions

    # Decisions
    total_decisions = await db.scalar(select(func.count(Decision.id))) or 0

    # Total tokens and cost
    total_tokens = await db.scalar(select(func.sum(Meeting.token_count))) or 0
    total_cost = await db.scalar(select(func.sum(Meeting.cost_usd))) or 0.0

    avg_cost = (total_cost / meetings_count) if meetings_count > 0 else 0.0

    return {
        "meetings": {
            "total": meetings_count,
            "completed": completed_meetings,
        },
        "action_items": {
            "total": total_actions,
            "completed": completed_actions,
            "pending": pending_actions,
        },
        "decisions": {
            "total": total_decisions,
        },
        "ai_usage": {
            "total_tokens": int(total_tokens),
            "total_cost_usd": round(float(total_cost), 4),
            "average_cost_per_meeting_usd": round(float(avg_cost), 4),
        },
    }
