"""
sa_resident_agent/api/routes.py

FastAPI route definitions.
Two agents are created at startup:
  - _agent         : Q&A mode (simulate_mode=False)
  - _simulate_agent: Guided enrollment simulation (simulate_mode=True)
"""

from __future__ import annotations

import logging

from fastapi import APIRouter

from sa_resident_agent.agent.agent import Agent
from sa_resident_agent.api.schemas import (
    ChatRequest,
    ChatResponse,
    HealthResponse,
    ResetRequest,
    ResetResponse,
    SimulateRequest,
    SimulateResponse,
    SourceDoc,
    StatusResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()

_agent: Agent | None = None
_simulate_agent: Agent | None = None


def set_agent(agent: Agent):
    global _agent
    _agent = agent


def set_simulate_agent(agent: Agent):
    global _simulate_agent
    _simulate_agent = agent


def get_agent() -> Agent:
    if _agent is None:
        raise RuntimeError("Agent not initialized.")
    return _agent


def get_simulate_agent() -> Agent:
    if _simulate_agent is None:
        raise RuntimeError("Simulate agent not initialized.")
    return _simulate_agent


# ---------------------------------------------------------------------------
# POST /chat  — Q&A mode
# ---------------------------------------------------------------------------

@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    """Send a user message and receive a RAG-grounded agent response."""
    agent = get_agent()
    logger.info(f"POST /chat  session={req.session_id}  message='{req.message[:60]}'")

    resp = agent.chat(session_id=req.session_id, message=req.message)

    checklist = {k: str(v).split(".")[-1] for k, v in resp.checklist.items()}

    return ChatResponse(
        session_id=resp.session_id,
        reply=resp.reply,
        intent=str(resp.intent).split(".")[-1],
        sources=[
            SourceDoc(url=s.url, provider=s.provider, chunk_preview=s.chunk_preview)
            for s in resp.sources
        ],
        checklist=checklist,
    )


# ---------------------------------------------------------------------------
# POST /simulate  — guided signup simulation mode
# ---------------------------------------------------------------------------

@router.post("/simulate", response_model=SimulateResponse)
def simulate(req: SimulateRequest):
    """
    Guided utility enrollment simulation.
    The agent walks the user through setting up CPS Energy, SAWS,
    and City of San Antonio services field by field.

    Use the same session_id across turns to maintain enrollment progress.
    Use POST /reset to restart the simulation from scratch.
    """
    agent = get_simulate_agent()
    logger.info(f"POST /simulate  session={req.session_id}  message='{req.message[:60]}'")

    resp = agent.chat(session_id=req.session_id, message=req.message)

    checklist        = {k: str(v).split(".")[-1] for k, v in resp.checklist.items()}
    collected_fields = agent.context.get_collected_fields(req.session_id)

    return SimulateResponse(
        session_id=resp.session_id,
        reply=resp.reply,
        intent="SIMULATE",
        checklist=checklist,
        collected_fields=collected_fields,
    )


# ---------------------------------------------------------------------------
# GET /status/{session_id}
# ---------------------------------------------------------------------------

@router.get("/status/{session_id}", response_model=StatusResponse)
def status(session_id: str):
    """Return checklist state and turn count for a session."""
    # Check both agents — session may be in either
    for agent in [get_agent(), get_simulate_agent()]:
        try:
            result   = agent.status(session_id)
            turn     = result["turn_count"]
            if turn > 0:
                checklist = {k: str(v).split(".")[-1] for k, v in result["checklist"].items()}
                return StatusResponse(
                    session_id=session_id,
                    checklist=checklist,
                    turn_count=turn,
                )
        except Exception:
            continue

    # Default — session not found in either agent
    result    = get_agent().status(session_id)
    checklist = {k: str(v).split(".")[-1] for k, v in result["checklist"].items()}
    return StatusResponse(
        session_id=session_id,
        checklist=checklist,
        turn_count=0,
    )


# ---------------------------------------------------------------------------
# POST /reset
# ---------------------------------------------------------------------------

@router.post("/reset", response_model=ResetResponse)
def reset(req: ResetRequest):
    """Clear session history and reset checklist to NOT_STARTED for both agents."""
    get_agent().reset(req.session_id)
    get_simulate_agent().reset(req.session_id)
    logger.info(f"POST /reset  session={req.session_id}")
    return ResetResponse(session_id=req.session_id, reset=True)


# ---------------------------------------------------------------------------
# GET /health
# ---------------------------------------------------------------------------

@router.get("/health", response_model=HealthResponse)
def health():
    """Liveness probe — returns ChromaDB doc count and LLM reachability."""
    agent         = get_agent()
    chroma_docs   = agent.retriever.store.count()
    llm_reachable = agent.llm.is_reachable()
    status        = "ok" if chroma_docs > 0 else "degraded"

    return HealthResponse(
        status=status,
        chroma_docs=chroma_docs,
        llm_reachable=llm_reachable,
    )
