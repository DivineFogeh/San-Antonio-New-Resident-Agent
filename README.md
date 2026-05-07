# SA New Resident Agent — Backend

FastAPI backend with PostgreSQL, Redis, and Docker.

## Quick Start

```bash
cp .env.example .env
docker-compose up -d
```

API docs: http://localhost:8000/docs

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | /api/user/session | Create/get user + seed checklist |
| GET | /api/user/{id} | Get user profile |
| GET | /api/checklist/{user_id} | Get progress (Redis-first) |
| PATCH | /api/checklist/{user_id} | Mark step complete/incomplete |
| GET | /api/services/cps | CPS Energy info |
| GET | /api/services/saws | SAWS info |
| GET | /api/services/city | City of SA info |
| POST | /api/services/submit/{service} | Submit form to service |
| WS | /ws/{user_id} | Real-time checklist updates |

## Stack

- **FastAPI** — async REST + WebSocket API
- **PostgreSQL** — user and checklist persistence
- **Redis** — checklist caching + session state
- **Docker Compose** — one command to run everything

## For Teammates

- Member 1 (crawler): POST cached knowledge to `/api/services/*` endpoints
- Member 2 (frontend): call `/api/user/session` on load, `/api/checklist/{id}` for state, `WS /ws/{id}` for live updates
