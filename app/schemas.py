# app/schemas.py — Pydantic request/response schemas
from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID
from datetime import datetime

# --- User ---
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    address: Optional[str] = None

class UserResponse(BaseModel):
    id: UUID
    name: str
    email: str
    address: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

# --- Checklist ---
class ChecklistUpdate(BaseModel):
    service: str    # "cps" | "saws" | "city"
    step: str       # "account" | "billing" | "docs"
    completed: bool

class ChecklistItemResponse(BaseModel):
    service: str
    step: str
    completed: bool
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True

# --- Services ---
class ServiceInfoResponse(BaseModel):
    provider: str
    signup_url: str
    phone: str
    docs_required: list[str]
    avg_processing: str

# --- Form Submission ---
class FormSubmitRequest(BaseModel):
    user_id: UUID
    service: str
    form_data: dict

class FormSubmitResponse(BaseModel):
    status: str
    confirmation: Optional[str] = None
    detail: Optional[str] = None
