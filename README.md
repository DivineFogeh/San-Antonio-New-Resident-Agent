# SA New Resident Agent

Full-stack AI assistant helping new San Antonio residents set up utilities with CPS Energy, SAWS, and the City of San Antonio.

---

## Project Structure

San-Antonio-New-Resident-Agent/
├── backend/          # Divine — FastAPI, PostgreSQL, Redis, Docker
└── crawler/          # Tobi — Web crawling, ChromaDB, AI Agent, LLM

---

## Backend (Divine)

FastAPI backend with PostgreSQL, Redis, and Docker.

### Quick Start
```bash
cd backend
cp .env.example .env
docker compose up -d
```
API docs: http://localhost:8000/docs

### Endpoints
| Method | Path | Description |
|--------|------|-------------|
| POST | /api/user/session | Create/get user + seed checklist |
| GET | /api/checklist/{user_id} | Get progress |
| PATCH | /api/checklist/{user_id} | Mark step complete |
| GET | /api/services/cps | CPS Energy info |
| GET | /api/services/saws | SAWS info |
| GET | /api/services/city | City of SA info |
| POST | /api/services/agent/chat | Q&A via AI agent |
| POST | /api/services/agent/simulate | Guided enrollment |
| WS | /ws/{user_id} | Real-time checklist updates |

---

## Crawler / AI Agent (Tobi)

Web crawling, ChromaDB knowledge base, and UTSA Llama LLM agent.

### Quick Start
```bash
cd crawler
cp .env.example .env
python main.py          # build ChromaDB index (run once, ~15 mins)
python server.py --host 0.0.0.0 --port 8001
```
API docs: http://localhost:8001/docs

### Endpoints
| Method | Path | Description |
|--------|------|-------------|
| POST | /chat | Q&A mode |
| POST | /simulate | Guided enrollment simulation |
| GET | /status/{session_id} | Checklist + turn count |
| POST | /reset | Clear session |
| GET | /health | Liveness probe |

---

## Environment Variables

### Backend `.env`
```dotenv
DATABASE_URL=postgresql+asyncpg://sa_user:sa_pass@localhost:5432/sa_agent
REDIS_URL=redis://localhost:6379
SECRET_KEY=change-me-in-production
AGENT_URL=http://localhost:8001
```

### Crawler `.env`
```dotenv
UTSA_LLM_BASE_URL=http://10.246.100.230/v1
UTSA_LLM_MODEL=llama-3.3-70b-instruct-awq
UTSA_LLM_API_KEY=your_key_here
CHROMA_PATH=data/chroma
LOG_LEVEL=INFO
```