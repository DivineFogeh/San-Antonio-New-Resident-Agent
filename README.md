# SA New Resident Agent

Full-stack conversational AI assistant helping new San Antonio residents set up utilities with CPS Energy, SAWS, and the City of San Antonio.

---

## Project Structure

```
San-Antonio-New-Resident-Agent/
├── backend/          # Oghenefejiro Fogeh — FastAPI, PostgreSQL, Redis, Docker
├── crawler/          # Tobi Oladunjoye — Web crawling, ChromaDB, AI Agent, LLM
├── frontend/         # Oluwakemi Ogunbameru — Web UI, Forms, Chat interface
├── docs/             # SPEC, STORIES, MODEL_CARD, LOGGING, REPRODUCE, DATA, MODELS
├── grading/          # traceability.yaml, manifest.yaml
├── scripts/          # regenerate.sh, regenerate_prompt.md
├── reports/          # git_contributions.txt
├── Makefile          # make reproduce, make test, make lint, make serve
├── CONTRIBUTIONS.md  # Team roles and contribution breakdown
└── README.md
```

---

## Quick Start (Full System)

**Requirements:** Docker Desktop, Python 3.11, UTSA VPN/WiFi, UTSA LLM API key

```bash
git clone https://github.com/DivineFogeh/San-Antonio-New-Resident-Agent.git
cd San-Antonio-New-Resident-Agent
```

**Terminal 1 — Backend:**
```bash
cd backend
cp .env.example .env
docker compose up -d
```
✅ Backend API: http://localhost:8000/docs

**Terminal 2 — Crawler/AI Agent:**
```bash
cd crawler
cp .env.example .env
# Add your UTSA_LLM_API_KEY to .env
python main.py          # build ChromaDB index (run once, ~15 mins)
python server.py --host 0.0.0.0 --port 8001
```
✅ Crawler API: http://localhost:8001/docs

**Terminal 3 — Frontend:**
```bash
cd frontend
python -m http.server 3000
# Open http://localhost:3000 in your browser
```
✅ Web UI: http://localhost:3000

---

## Team

| Member | Role | Module |
|--------|------|--------|
| Oghenefejiro Fogeh | Backend / Infrastructure / Service Integrations | `backend/` |
| Tobi Oladunjoye | Web Crawling / Knowledge Base / AI Agent | `crawler/` |
| Oluwakemi Ogunbameru | Form Engine / Frontend / Chat UI | `frontend/` |

---

## Backend (Oghenefejiro)

FastAPI backend with PostgreSQL, Redis, and Docker. Manages user sessions, checklist progress, and routes frontend requests to the AI agent.

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | /api/user/session | Create/get user + seed 9 checklist items |
| GET | /api/user/{user_id} | Get user profile |
| GET | /api/checklist/{user_id} | Get progress (Redis-first, DB fallback) |
| PATCH | /api/checklist/{user_id} | Mark step complete/incomplete |
| GET | /api/services/cps | CPS Energy info |
| GET | /api/services/saws | SAWS info |
| GET | /api/services/city | City of SA info |
| POST | /api/services/submit/{service} | Submit form to service |
| POST | /api/services/agent/chat | Q&A via AI agent |
| POST | /api/services/agent/simulate | Guided enrollment simulation |
| GET | /api/services/agent/status/{session_id} | Session checklist state |
| POST | /api/services/agent/reset | Reset session |
| WS | /ws/{user_id} | Real-time checklist updates |
| GET | / | Health check |

### Stack
- **FastAPI** — async REST + WebSocket API
- **PostgreSQL** — user and checklist persistence
- **Redis** — checklist caching + session state
- **Docker Compose** — one command to run everything

---

## Crawler / AI Agent (Tobi)

Web crawling, ChromaDB knowledge base, and UTSA Llama LLM agent. Exposes RAG-powered Q&A and guided enrollment simulation.

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | /chat | Q&A mode — RAG-grounded answers |
| POST | /simulate | Guided enrollment simulation |
| GET | /status/{session_id} | Checklist + turn count |
| POST | /reset | Clear session history |
| GET | /health | Liveness probe (ChromaDB + LLM status) |

### Stack
- **Playwright + BeautifulSoup** — web crawling
- **ChromaDB** — vector store (706 chunks)
- **sentence-transformers/all-MiniLM-L6-v2** — embeddings
- **LangChain** — RAG pipeline
- **UTSA Llama 3.3 70B** — LLM (UTSA network required)

---

## Frontend (Oluwakemi)

Web-based UI with multi-step enrollment forms, AI chat interface, and live progress dashboard.

### How to run

```bash
cd frontend
python -m http.server 3000
# Open http://localhost:3000 in your browser
# Make sure the backend is running at http://localhost:8000 first
```

### Features
- Multi-step validated forms for CPS Energy, SAWS, and City of SA
- AI chat interface connected to backend agent
- Live progress dashboard with completion tracking
- Form data synced to backend on submission

---

## Environment Variables

### Backend `backend/.env`
```dotenv
DATABASE_URL=postgresql+asyncpg://sa_user:sa_pass@db:5432/sa_agent
REDIS_URL=redis://redis:6379
SECRET_KEY=change-me-in-production
AGENT_URL=http://localhost:8001
```

### Crawler `crawler/.env`
```dotenv
UTSA_LLM_BASE_URL=http://10.246.100.230/v1
UTSA_LLM_MODEL=llama-3.3-70b-instruct-awq
UTSA_LLM_API_KEY=your_key_here
CHROMA_PATH=data/chroma
LOG_LEVEL=INFO
```

---

## Results

| Metric | Value | Tolerance |
|--------|-------|-----------|
| ChromaDB chunks indexed | 706 | ±50 |
| Test coverage | 78% | ≥70% |
| User story pass rate | 100% (8/8 automated) | ≥90% |
| Total tests passing | 110/110 | — |
| Load test RPS | 12.4 req/s | ≥10 req/s |
| Load test error rate | 2.1% | ≤5% |
| LLM response time (median) | 1,243ms | — |
| Backend startup time | <2 min | <10 min |

---

## Documentation

| File | Description |
|------|-------------|
| `docs/SPEC.md` | Full system specification |
| `docs/STORIES.md` | User stories with manual walkthrough steps |
| `docs/REPRODUCE.md` | Full reproduction guide |
| `docs/DATA.md` | Data sources and vector store documentation |
| `docs/MODELS.md` | LLM and embedding model documentation |
| `docs/MODEL_CARD.md` | Intended use, limitations, risks |
| `docs/LOGGING.md` | Structured logging guide with worked example |
| `docs/usage.md` | Usage guide per story |
| `docs/diagrams/architecture.png` | System architecture diagram |
| `grading/traceability.yaml` | Story → module → test mapping |
| `grading/manifest.yaml` | Pinned versions and reproducibility manifest |
| `CONTRIBUTIONS.md` | Team roles and contribution breakdown |