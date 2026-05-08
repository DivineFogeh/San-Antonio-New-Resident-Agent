# app/api/routes/checklist.py — Progress tracking endpoints
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db import get_db
from app.models import ChecklistItem
from app.cache import cache_set, cache_get, cache_delete
from app.schemas import ChecklistUpdate, ChecklistItemResponse
from datetime import datetime
import json

router = APIRouter()

@router.get("/{user_id}", response_model=list[ChecklistItemResponse])
async def get_checklist(user_id: str, db: AsyncSession = Depends(get_db)):
    """Get all checklist items. Redis-first, DB fallback."""
    cached = await cache_get(f"checklist:{user_id}")
    if cached:
        return json.loads(cached)

    result = await db.execute(
        select(ChecklistItem).where(ChecklistItem.user_id == user_id)
    )
    items = result.scalars().all()
    if not items:
        raise HTTPException(404, "No checklist found for this user")

    data = [
        {
            "service": i.service,
            "step": i.step,
            "completed": i.completed,
            "completed_at": i.completed_at.isoformat() if i.completed_at else None
        }
        for i in items
    ]
    await cache_set(f"checklist:{user_id}", json.dumps(data), ttl=300)
    return data

@router.patch("/{user_id}")
async def update_checklist(
    user_id: str,
    payload: ChecklistUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Mark a checklist step complete or incomplete."""
    result = await db.execute(
        select(ChecklistItem).where(
            ChecklistItem.user_id == user_id,
            ChecklistItem.service == payload.service,
            ChecklistItem.step    == payload.step
        )
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(404, "Checklist item not found")

    item.completed    = payload.completed
    item.completed_at = datetime.utcnow() if payload.completed else None
    await db.commit()

    # Bust cache so frontend gets fresh data
    await cache_delete(f"checklist:{user_id}")
    return {"status": "updated", "service": payload.service, "step": payload.step}
