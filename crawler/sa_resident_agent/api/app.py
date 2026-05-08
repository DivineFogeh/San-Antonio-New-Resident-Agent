"""
sa_resident_agent/api/app.py

FastAPI application factory.
Creates two Agent instances at startup:
  - Q&A agent      (simulate_mode=False) → serves POST /chat
  - Simulate agent (simulate_mode=True)  → serves POST /simulate
"""

from __future__ import annotations

import logging
import os
import sys
import uuid
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from sa_resident_agent.agent.agent import Agent
from sa_resident_agent.api.routes import router, set_agent, set_simulate_agent
from sa_resident_agent.llm.utsa_client import UTSAClient

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logging.getLogger("chromadb.telemetry.product.posthog").setLevel(logging.CRITICAL)
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

CHROMA_PATH = os.getenv("CHROMA_PATH", "data/chroma")


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting SA Resident Agent API...")

    llm = UTSAClient()

    # Q&A agent
    qa_agent = Agent(chroma_path=CHROMA_PATH, llm=llm, simulate_mode=False)
    set_agent(qa_agent)

    # Simulate agent — shares same LLM client and ChromaDB but separate session state
    sim_agent = Agent(chroma_path=CHROMA_PATH, llm=llm, simulate_mode=True)
    set_simulate_agent(sim_agent)

    doc_count = qa_agent.retriever.store.count()
    logger.info(f"ChromaDB ready — {doc_count} chunks loaded")
    logger.info(f"UTSA LLM reachable: {llm.is_reachable()}")
    logger.info("Q&A agent ready      → POST /chat")
    logger.info("Simulate agent ready → POST /simulate")

    yield

    logger.info("Shutting down SA Resident Agent API...")
    llm.close()


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

def create_app() -> FastAPI:
    app = FastAPI(
        title="SA Resident Agent API",
        description=(
            "Conversational AI assistant that helps new San Antonio residents "
            "set up utilities with CPS Energy, SAWS, and the City of San Antonio.\n\n"
            "**Two modes:**\n"
            "- `POST /chat` — Q&A mode: ask questions, get RAG-grounded answers\n"
            "- `POST /simulate` — Guided enrollment: step-by-step signup simulation"
        ),
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        request_id = str(uuid.uuid4())[:8]
        logger.info(f"REQUEST  id={request_id} method={request.method} path={request.url.path}")
        start    = time.time()
        response = await call_next(request)
        duration = round((time.time() - start) * 1000)
        logger.info(f"RESPONSE id={request_id} status={response.status_code} duration={duration}ms")
        return response

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.exception(f"Unhandled exception on {request.url.path}: {exc}")
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error — check server logs."},
        )

    app.include_router(router)
    return app
