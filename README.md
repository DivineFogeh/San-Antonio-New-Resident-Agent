# SA Resident Agent — Backend Integration Guide

> **For:** Teammate 1 (Backend / Infrastructure / Docker)  
> **Written by:** Tobi (Web Crawling / Knowledge Base / AI Agent Layer)  
> **Last updated:** May 2026

---

## What This Module Does

This module is the core AI layer of the SA Resident Agent. It:

1. **Crawls** CPS Energy, SAWS, and City of San Antonio websites and indexes them into a local ChromaDB vector database
2. **Exposes a FastAPI HTTP server** that the frontend calls for all AI interactions
3. **Handles two modes:**
   - `POST /chat` — Q&A mode: user asks questions, agent retrieves relevant content and answers with the UTSA Llama LLM
   - `POST /simulate` — Guided enrollment simulation: step-by-step utility signup walkthrough

---

## Project Structure (My Components)

```
NLP_PROJECT/
├── main.py                          # Builds the ChromaDB index (run once)
├── server.py                        # Starts the FastAPI server
├── agent_test.py                    # Terminal tester (dev only)
├── query.py                         # Terminal retrieval tester (dev only)
├── setup.py                         # Package install config
├── requirements.txt                 # All Python dependencies
├── Makefile                         # make reproduce / make test / make lint
├── pytest.ini                       # Test config (≥70% coverage required)
├── .env.example                     # Copy to .env and fill in values
│
├── data/chroma/                     # ChromaDB index (generated, not in git)
│
├── sa_resident_agent/
│   ├── crawlers/                    # Web crawlers (CPS, SAWS, City of SA)
│   ├── knowledge/                   # Chunker, embedder, vector store, retriever
│   ├── agent/                       # Intent classifier, prompts, context, orchestrator
│   ├── llm/                         # UTSA Llama HTTP client
│   └── api/                         # FastAPI routes, schemas, app factory
│
└── tests/                           # 110 tests — unit, integration, edge, user stories
```

---

## Environment Setup

### 1. Conda environment (UTSA HPC)

```bash
conda activate newenv
export LD_PRELOAD=/work/dyt875/.conda_envs/newenv/lib/libstdc++.so.6
```

> **Note:** The `LD_PRELOAD` line is required every session on the HPC due to a system `libstdc++` version mismatch. Add it to `~/.bashrc` to make it permanent.

### 2. Install dependencies

```bash
pip install -r requirements.txt
pip install -e .
playwright install chromium
```

### 3. Environment variables

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Contents of `.env`:

```dotenv
UTSA_LLM_BASE_URL=http://10.246.100.230/v1
UTSA_LLM_MODEL=llama-3.3-70b-instruct-awq
UTSA_LLM_API_KEY=your_key_here        # get from professor
CHROMA_PATH=data/chroma
LOG_LEVEL=INFO
```

> **Important:** The UTSA LLM endpoint requires an API key and only works on the UTSA network or VPN.

---

## Building the Knowledge Base (Run Once)

Before starting the server, the ChromaDB index must be built:

```bash
python main.py
```

This crawls all three provider websites, embeds the content, and persists it to `data/chroma/`. Takes 5–15 minutes. The index is already built at `data/chroma/` with 1,423 chunks — only re-run if you need to refresh it.

To rebuild a specific provider:

```bash
python main.py --providers CPS_ENERGY --rebuild
```

---

## Starting the API Server

```bash
python server.py --host 0.0.0.0 --port 8000
```

On startup you should see:

```
Starting SA Resident Agent API...
ChromaDB ready — 1423 chunks loaded
UTSA LLM reachable: True
Q&A agent ready      → POST /chat
Simulate agent ready → POST /simulate
```

Swagger UI is available at `http://localhost:8000/docs`.

---

## API Endpoints

### `POST /chat` — Q&A Mode

**Request:**
```json
{
  "session_id": "string",
  "message": "string"
}
```

**Response:**
```json
{
  "session_id": "string",
  "reply": "string",
  "intent": "QUESTION | FORM_HELP | STATUS",
  "sources": [
    {
      "url": "string",
      "provider": "CPS_ENERGY | SAWS | CITY_SA",
      "chunk_preview": "string"
    }
  ],
  "checklist": {
    "CPS_ENERGY": "NOT_STARTED | IN_PROGRESS | COMPLETE",
    "SAWS": "NOT_STARTED | IN_PROGRESS | COMPLETE",
    "CITY_SA": "NOT_STARTED | IN_PROGRESS | COMPLETE"
  },
  "validated_slots": {}
}
```

**Errors:**
- `422` — missing or empty `session_id` or `message`
- `500` — internal server error (check logs)

---

### `POST /simulate` — Guided Enrollment Simulation

**Request:**
```json
{
  "session_id": "string",
  "message": "string"
}
```

**Response:**
```json
{
  "session_id": "string",
  "reply": "string",
  "intent": "SIMULATE",
  "checklist": {
    "CPS_ENERGY": "NOT_STARTED | IN_PROGRESS | COMPLETE",
    "SAWS": "NOT_STARTED | IN_PROGRESS | COMPLETE",
    "CITY_SA": "NOT_STARTED | IN_PROGRESS | COMPLETE"
  },
  "collected_fields": {
    "cps_name": "John Doe",
    "cps_service_addr": "123 Main St, San Antonio, TX 78201"
  }
}
```

> The `collected_fields` object contains all form data collected so far. Your frontend can use this to pre-fill form fields.

---

### `GET /status/{session_id}`

Returns checklist state and turn count for any session (works for both `/chat` and `/simulate` sessions).

**Response:**
```json
{
  "session_id": "string",
  "checklist": {
    "CPS_ENERGY": "NOT_STARTED | IN_PROGRESS | COMPLETE",
    "SAWS": "NOT_STARTED | IN_PROGRESS | COMPLETE",
    "CITY_SA": "NOT_STARTED | IN_PROGRESS | COMPLETE"
  },
  "turn_count": 5
}
```

---

### `POST /reset`

Clears session history, checklist, and collected fields for both agents.

**Request:**
```json
{ "session_id": "string" }
```

**Response:**
```json
{ "session_id": "string", "reset": true }
```

---

### `GET /health`

Liveness probe for Docker health check.

**Response:**
```json
{
  "status": "ok",
  "chroma_docs": 1423,
  "llm_reachable": true
}
```

---

## Docker Integration

For Docker, start the server on `0.0.0.0` so it's reachable from other containers:

```bash
python server.py --host 0.0.0.0 --port 8000
```

### Recommended `docker-compose.yml` service block:

```yaml
agent:
  build: .
  command: python server.py --host 0.0.0.0 --port 8000
  ports:
    - "8000:8000"
  environment:
    - UTSA_LLM_BASE_URL=http://10.246.100.230/v1
    - UTSA_LLM_MODEL=llama-3.3-70b-instruct-awq
    - UTSA_LLM_API_KEY=${UTSA_LLM_API_KEY}
    - CHROMA_PATH=/app/data/chroma
    - LOG_LEVEL=INFO
  volumes:
    - ./data/chroma:/app/data/chroma
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
    interval: 30s
    timeout: 10s
    retries: 3
  depends_on: []
```

> **Important:** Mount `data/chroma` as a volume so the index persists across container restarts. Do NOT rebuild the index inside Docker on every startup — it takes 15 minutes.

---

## Makefile Targets

```bash
make reproduce    # Rebuild ChromaDB index from scratch (used by TA grading script)
make test         # Run 110 tests with coverage report (≥70% required)
make test-fast    # Run tests without coverage (faster)
make lint         # Run ruff linter
make serve        # Start server on 0.0.0.0:8000
make preflight    # Full sanity check before grading
make clean        # Remove ChromaDB, coverage, pycache
```

---

## Session Management Notes

- Sessions are **in-memory only** — restarting the server clears all sessions
- `/chat` and `/simulate` maintain **separate** session stores — use different `session_id` prefixes if needed (e.g. `qa-001` vs `sim-001`)
- `/reset` clears both stores for a given session ID
- `session_id` is caller-supplied — your backend or frontend should generate and manage these (UUID recommended)

---

## Running Tests

```bash
make test
```

All 110 tests use a mock LLM — no UTSA network required to run tests.

---

## Known Issues / Notes for Integration

- The UTSA LLM endpoint returns `401` without a valid API key — get the key from the professor
- The `libstdc++` `LD_PRELOAD` fix is required every HPC session (see Environment Setup above)
- ChromaDB telemetry errors in logs are harmless — telemetry is disabled in code
- `HuggingFace resume_download` warnings are harmless — third-party deprecation notice
- The embedding model (`all-MiniLM-L6-v2`, ~90MB) downloads automatically on first run