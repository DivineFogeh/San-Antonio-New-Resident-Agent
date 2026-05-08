# app/api/routes/user.py — User session endpoints
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db import get_db
from app.models import User, ChecklistItem
from app.schemas import UserCreate, UserResponse

router = APIRouter()

SERVICES = ["cps", "saws", "city"]
STEPS    = ["account", "billing", "docs"]

@router.post("/session", response_model=UserResponse)
async def create_or_get_user(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    """Create a new user session and seed their checklist."""
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()

    if not user:
        user = User(name=payload.name, email=payload.email, address=payload.address)
        db.add(user)
        await db.flush()

        # Seed checklist items for all 3 services
        for service in SERVICES:
            for step in STEPS:
                db.add(ChecklistItem(user_id=user.id, service=service, step=step))

        await db.commit()
        await db.refresh(user)

    return user

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User not found")
    return user
