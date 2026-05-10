# SA New Resident Agent — System Specification

**Version:** 1.0
**Project:** CS 6263 NLP and Agentic AI — Final Project
**Team:** Divine Fejiro (Backend/Infrastructure), Tobi (Web Crawling/Knowledge Base/AI Agent), Kemi Ogunbameru (Form Engine/Frontend/Chat UI)

---

## 1. Purpose

The SA New Resident Agent is a full-stack conversational AI system that guides new San Antonio residents through utility enrollment with CPS Energy, SAWS (San Antonio Water System), and the City of San Antonio. The system consists of three integrated layers:

1. **Web Crawling & Knowledge Base (Tobi):** Crawls official service-provider websites, chunks and embeds content into a ChromaDB vector store, and exposes a RAG-powered FastAPI agent at `POST /chat` and `POST /simulate`.

2. **Backend Infrastructure & Service Integrations (Divine):** A FastAPI backend with PostgreSQL and Redis that manages user sessions, checklist progress, and routes frontend requests to the AI agent and service integrations. Runs in Docker Compose.

3. **Form Engine & Frontend/Chat UI (Kemi):** A Jupyter/Colab-based interactive frontend with multi-step validated forms for all three services, a live progress dashboard, and an AI chat interface connected to the backend.

Users can ask natural-language questions about rates, required documents, and enrollment steps. The agent retrieves grounded answers from indexed content, tracks per-session progress, and returns structured responses the form engine acts on.

---

## 2. Component Inventory

### 2.1 Backend (Divine)

| Component | Description | Module Path |
|---|---|---|
| FastAPI App | Main entry point, CORS, startup hooks | `backend/app/main.py` |
| User Routes | Session creation, user profile | `backend/app/api/routes/user.py` |
| Checklist Routes | Progress tracking endpoints | `backend/app/api/routes/checklist.py` |
| Service Routes | CPS, SAWS, City SA info + agent proxy | `backend/app/api/routes/services.py` |
| WebSocket Routes | Real-time checklist updates | `backend/app/api/routes/ws.py` |
| DB Connection | Async PostgreSQL via SQLAlchemy | `backend/app/db.py` |
| Redis Cache | Session and checklist caching | `backend/app/cache.py` |
| User/Checklist Models | SQLAlchemy ORM models | `backend/app/models.py` |
| Pydantic Schemas | Request/response validation | `backend/app/schemas.py` |
| Config | Environment settings | `backend/app/config.py` |
| CPS Energy Service | CPS info and enrollment integration | `backend/app/services/cps_energy.py` |
| SAWS Service | SAWS info and enrollment integration | `backend/app/services/saws.py` |
| City SA Service | City of SA info and enrollment integration | `backend/app/services/city_sa.py` |
| Agent Service | Proxy to AI agent (chat, simulate, status, reset) | `backend/app/services/agent.py` |

### 2.2 Crawler / AI Agent (Tobi)

| Component | Description | Module Path |
|---|---|---|
| CPS Energy Crawler | Crawls and parses CPS Energy service pages | `crawler/sa_resident_agent/crawlers/cps_crawler.py` |
| SAWS Crawler | Crawls and parses SAWS service pages | `crawler/sa_resident_agent/crawlers/saws_crawler.py` |
| City of SA Crawler | Crawls and parses City of SA pages | `crawler/sa_resident_agent/crawlers/city_crawler.py` |
| Base Crawler | Shared Playwright + BeautifulSoup logic | `crawler/sa_resident_agent/crawlers/base_crawler.py` |
| Document Chunker | Splits raw HTML into overlapping chunks | `crawler/sa_resident_agent/knowledge/chunker.py` |
| Embedder | Encodes chunks using all-MiniLM-L6-v2 | `crawler/sa_resident_agent/knowledge/embedder.py` |
| ChromaDB Store | Persists and queries the vector index | `crawler/sa_resident_agent/knowledge/vector_store.py` |
| Index Builder | Orchestrates crawl → chunk → embed → store | `crawler/sa_resident_agent/knowledge/index_builder.py` |
| Retriever | Wraps ChromaDB for top-k semantic search | `crawler/sa_resident_agent/knowledge/retriever.py` |
| Intent Classifier | Classifies user turn as QUESTION, FORM_HELP, or STATUS | `crawler/sa_resident_agent/agent/intent.py` |
| Prompt Templates | Jinja2 templates for RAG QA and form guidance | `crawler/sa_resident_agent/agent/prompts.py` |
| Context Manager | Per-session conversation history and checklist state | `crawler/sa_resident_agent/agent/context.py` |
| LangChain Agent | Orchestrates retrieval, intent routing, LLM call | `crawler/sa_resident_agent/agent/agent.py` |
| Agent API | FastAPI app exposing /chat, /simulate, /status, /reset | `crawler/sa_resident_agent/api/routes.py` |
| UTSA LLM Client | Wrapper around UTSA Llama HTTP endpoint | `crawler/sa_resident_agent/llm/utsa_client.py` |

### 2.3 Frontend (Kemi)

| Component | Description | Module Path |
|---|---|---|
| Chat Interface | AI chat UI connected to backend /agent/chat | `frontend/sa_new_resident_agent.py` |
| Form Engine | Multi-step validated forms for CPS, SAWS, City SA | `frontend/sa_new_resident_agent.py` |
| Progress Dashboard | Live checklist dashboard synced to backend | `frontend/sa_new_resident_agent.py` |
| Backend Connector | HTTP client connecting frontend to backend API | `frontend/sa_new_resident_agent.py` |

---

## 3. Data Flow

```
User (Kemi's Frontend / Colab Notebook)
        │
        ▼
Backend FastAPI (localhost:8000)
  ├── POST /api/user/session      → create user + seed checklist (PostgreSQL)
  ├── GET  /api/checklist/{id}    → fetch progress (Redis cache → PostgreSQL)
  ├── PATCH /api/checklist/{id}   → mark step complete
  ├── POST /api/services/agent/chat     ──┐
  └── POST /api/services/agent/simulate ──┤
                                          ▼
                            Crawler FastAPI (localhost:8001)
                              ├── POST /chat
                              │     ├── Intent Classifier
                              │     ├── Retriever (ChromaDB)
                              │     ├── Prompt Templates
                              │     └── UTSA Llama LLM
                              ├── POST /simulate
                              ├── GET  /status/{session_id}
                              └── POST /reset
```

**Index Build Flow (offline / `make reproduce`):**
```
Playwright browser → Base Crawler → CPS / SAWS / City Crawlers
    → Raw HTML + metadata
    → Document Chunker (chunk_size=512, overlap=64)
    → Embedder (all-MiniLM-L6-v2, dim=384)
    → ChromaDB (persisted at crawler/data/chroma/)
```

---

## 4. Public Interfaces

### 4.1 Backend API (localhost:8000)

#### POST /api/user/session
Create or retrieve a user session and seed checklist.

**Request:**
```json
{ "name": "string", "email": "string", "address": "string" }
```
**Response:**
```json
{ "id": "uuid", "name": "string", "email": "string", "created_at": "datetime" }
```

#### GET /api/checklist/{user_id}
Get all checklist items. Redis-first, DB fallback.

**Response:**
```json
[{ "service": "cps|saws|city", "step": "account|billing|docs", "completed": true }]
```

#### PATCH /api/checklist/{user_id}
Mark a checklist step complete or incomplete.

**Request:**
```json
{ "service": "cps", "step": "account", "completed": true }
```

#### POST /api/services/agent/chat
Proxy to AI agent Q&A mode.

**Request:**
```json
{ "session_id": "string", "message": "string" }
```
**Response:**
```json
{
  "status": "success",
  "data": {
    "session_id": "string",
    "reply": "string",
    "intent": "QUESTION|FORM_HELP|STATUS",
    "sources": [{ "url": "string", "provider": "string", "chunk_preview": "string" }],
    "checklist": { "CPS_ENERGY": "NOT_STARTED|IN_PROGRESS|COMPLETE" }
  }
}
```

#### POST /api/services/agent/simulate
Proxy to guided enrollment simulation mode.

#### GET /api/services/agent/status/{session_id}
Get session checklist state and turn count.

#### POST /api/services/agent/reset
Reset session history and checklist.

#### WS /ws/{user_id}
WebSocket for real-time checklist updates.

### 4.2 Crawler API (localhost:8001)

See Section 4.1 of Tobi's crawler spec for full crawler interface definitions including POST /chat, POST /simulate, GET /status/{session_id}, POST /reset, GET /health.

---

## 5. Model and Prompt Selection

### 5.1 LLM

| Property | Value |
|---|---|
| Model | `llama-3.3-70b-instruct-awq` (UTSA hosted endpoint) |
| Temperature | `0.2` |
| Max tokens | `512` |
| Endpoint | `http://10.246.100.230/v1` (UTSA network only) |
| Env var | `UTSA_LLM_BASE_URL` |

### 5.2 Embedding Model

| Property | Value |
|---|---|
| Model | `sentence-transformers/all-MiniLM-L6-v2` |
| Dimensions | 384 |
| Runtime | Local CPU |

### 5.3 Prompt Templates

**RAG QA Prompt:**
```
You are a helpful assistant for new San Antonio residents setting up utilities.
Answer the user's question using only the context below. If the answer is not in
the context, say "I don't have that information — please visit {provider_url}."
Do not make up rates, deadlines, or document requirements.

Context: {retrieved_chunks}
Conversation history: {history}
User: {user_message}
Assistant:
```

**Intent Classification Prompt:**
```
Classify the following user message into exactly one of: QUESTION, FORM_HELP, STATUS.
- QUESTION: user is asking about rates, policies, documents, or requirements
- FORM_HELP: user is filling out a form or needs field-level guidance
- STATUS: user is asking about their setup progress or checklist
Respond with only the label.
Message: {user_message}
```

### 5.4 Chunking Parameters

| Parameter | Value |
|---|---|
| Chunk size | 512 tokens |
| Overlap | 64 tokens |
| Splitter | RecursiveCharacterTextSplitter (LangChain) |
| Metadata | url, provider, scraped_at, chunk_index |
