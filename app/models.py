# app/models.py — SQLAlchemy database models
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db import Base
from datetime import datetime
import uuid

class User(Base):
    __tablename__ = "users"

    id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name       = Column(String, nullable=False)
    email      = Column(String, unique=True, index=True)
    address    = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    checklist  = relationship("ChecklistItem", back_populates="user", cascade="all, delete")

class ChecklistItem(Base):
    __tablename__ = "checklist_items"

    id           = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id      = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    service      = Column(String, nullable=False)   # "cps" | "saws" | "city"
    step         = Column(String, nullable=False)   # "account" | "billing" | "docs"
    completed    = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="checklist")
