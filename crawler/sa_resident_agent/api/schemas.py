"""
sa_resident_agent/api/schemas.py

Pydantic request and response models.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# POST /chat
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    session_id: str  = Field(..., min_length=1, description="Unique session identifier")
    message:    str  = Field(..., min_length=1, description="User message")


class SourceDoc(BaseModel):
    url:           str
    provider:      str
    chunk_preview: str


class ChatResponse(BaseModel):
    session_id:      str
    reply:           str
    intent:          str
    sources:         list[SourceDoc]
    checklist:       dict[str, str]
    validated_slots: dict[str, str] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# POST /simulate
# ---------------------------------------------------------------------------

class SimulateRequest(BaseModel):
    session_id: str = Field(..., min_length=1, description="Unique session identifier")
    message:    str = Field(..., min_length=1, description="User message in simulation mode")


class SimulateResponse(BaseModel):
    session_id:       str
    reply:            str
    intent:           str = "SIMULATE"
    checklist:        dict[str, str]
    collected_fields: dict[str, str] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# GET /status/{session_id}
# ---------------------------------------------------------------------------

class StatusResponse(BaseModel):
    session_id:  str
    checklist:   dict[str, str]
    turn_count:  int


# ---------------------------------------------------------------------------
# POST /reset
# ---------------------------------------------------------------------------

class ResetRequest(BaseModel):
    session_id: str = Field(..., min_length=1)


class ResetResponse(BaseModel):
    session_id: str
    reset:      bool


# ---------------------------------------------------------------------------
# GET /health
# ---------------------------------------------------------------------------

class HealthResponse(BaseModel):
    status:        str
    chroma_docs:   int
    llm_reachable: bool
