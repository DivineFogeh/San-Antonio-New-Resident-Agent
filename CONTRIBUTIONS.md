# Team Contributions

## Team Members

| Member | Role | Modules Owned | Contribution % |
|---|---|---|---|
| Oghenefejiro Fogeh | Backend / Infrastructure / Service Integrations | `backend/` | 34% |
| Tobi Oladunjoye | Web Crawling / Knowledge Base / AI Agent Layer | `crawler/` | 33% |
| Oluwakemi Ogunbameru | Form Engine / Frontend / Chat UI | `frontend/` | 33% |

---

## Divine Fejiro — Backend / Infrastructure / Service Integrations (34%)

**Modules owned:**
- `backend/app/main.py` — FastAPI entry point, CORS, startup hooks
- `backend/app/api/routes/user.py` — User session creation and retrieval
- `backend/app/api/routes/checklist.py` — Checklist progress tracking
- `backend/app/api/routes/services.py` — CPS, SAWS, City SA info + AI agent proxy
- `backend/app/api/routes/ws.py` — WebSocket real-time updates
- `backend/app/db.py` — Async PostgreSQL connection
- `backend/app/cache.py` — Redis caching layer
- `backend/app/models.py` — SQLAlchemy ORM models
- `backend/app/schemas.py` — Pydantic request/response schemas
- `backend/app/config.py` — Environment configuration
- `backend/app/services/cps_energy.py` — CPS Energy integration
- `backend/app/services/saws.py` — SAWS integration
- `backend/app/services/city_sa.py` — City of SA integration
- `backend/app/services/agent.py` — AI agent proxy service
- `backend/docker-compose.yml` — Docker Compose orchestration
- `backend/Dockerfile` — Container definition
- `docs/SPEC.md`, `docs/STORIES.md`, `docs/REPRODUCE.md` — Project documentation
- `grading/` — Grading artifacts
- `scripts/` — Automation scripts

**Key contributions:**
- Designed and implemented the full REST API with PostgreSQL persistence and Redis caching
- Set up Docker Compose with PostgreSQL, Redis, and FastAPI containers
- Integrated the backend with Tobi's AI agent via HTTP proxy routes
- Connected Kemi's frontend to the backend by updating her notebook
- Managed GitHub repository, branch strategy, and code merges
- Created all project documentation (SPEC, STORIES, REPRODUCE, MODEL_CARD, etc.)

---

## Tobi — Web Crawling / Knowledge Base / AI Agent Layer (33%)

**Modules owned:**
- `crawler/sa_resident_agent/crawlers/` — CPS, SAWS, City SA web crawlers
- `crawler/sa_resident_agent/knowledge/` — Chunker, embedder, vector store, retriever
- `crawler/sa_resident_agent/agent/` — Intent classifier, prompts, context, orchestrator
- `crawler/sa_resident_agent/llm/` — UTSA Llama HTTP client
- `crawler/sa_resident_agent/api/` — FastAPI routes, schemas, app factory
- `crawler/tests/` — Unit, integration, edge, user story tests
- `crawler/main.py` — Index builder entry point
- `crawler/server.py` — API server entry point
- `crawler/spec.md`, `crawler/stories.md` — Crawler-layer specification

**Key contributions:**
- Built Playwright-based web crawlers for all three SA utility providers
- Implemented ChromaDB vector store with sentence-transformers embeddings
- Designed and implemented the RAG agent with intent classification
- Built UTSA Llama LLM client with retry logic
- Wrote 110 tests covering unit, integration, edge cases, and user stories
- Implemented guided enrollment simulation mode

---

## Kemi Ogunbameru — Form Engine / Frontend / Chat UI (33%)

**Modules owned:**
- `frontend/sa_new_resident_agent.py` — Full frontend application

**Key contributions:**
- Designed and implemented multi-step validated enrollment forms for CPS Energy, SAWS, and City of SA
- Built AI chat interface with quick-action buttons and conversation history
- Created live progress dashboard showing completion status for all three services
- Implemented field-level validation (SSN format, ZIP code, email, phone)
- Integrated frontend with backend API for chat, form submission, and checklist sync
- Designed session management with unique UUID per user run
