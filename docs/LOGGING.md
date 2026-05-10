# Logging Guide

## Overview

The SA New Resident Agent uses structured logging throughout. Every request is tagged with a unique `request_id` that propagates through all components, allowing the TA to trace a single request end to end through `docker compose logs`.

## Log Format

All log entries are structured JSON with the following fields:

```json
{
  "timestamp": "2026-05-08T20:53:38.123Z",
  "level": "INFO",
  "module": "sa_resident_agent.api.app",
  "request_id": "a1b2c3d4",
  "message": "POST /chat received",
  "session_id": "test-us01",
  "duration_ms": 1243
}
```

## Tracing a Request End to End

### Step 1 — Bring up the systems

```bash
cd backend && docker compose up -d
cd crawler && python server.py --host 0.0.0.0 --port 8001
```

### Step 2 — Send a request

```bash
curl -X POST http://localhost:8000/api/services/agent/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "trace-demo", "message": "How do I set up CPS Energy?"}'
```

### Step 3 — View logs

```bash
docker compose logs -f api
```

### Step 4 — Find the request ID

In the backend logs you will see:

```
api-1  | 2026-05-08T20:53:38 [INFO] app — REQUEST  id=a1b2c3d4 method=POST path=/api/services/agent/chat
api-1  | 2026-05-08T20:53:38 [INFO] app — Forwarding to agent: session=trace-demo
api-1  | 2026-05-08T20:53:39 [INFO] app — Agent response received: 1243ms
api-1  | 2026-05-08T20:53:39 [INFO] app — RESPONSE id=a1b2c3d4 status=200 duration=1243ms
```

In the crawler logs you will see:

```
2026-05-08T20:53:38 [INFO] sa_resident_agent.api.app — REQUEST id=a1b2c3d4 method=POST path=/chat
2026-05-08T20:53:38 [INFO] sa_resident_agent.api.routes — POST /chat session=trace-demo message='How do I set up CPS Energy?'
2026-05-08T20:53:38 [INFO] sa_resident_agent.agent.intent — Classified intent: QUESTION
2026-05-08T20:53:38 [INFO] sa_resident_agent.knowledge.retriever — Retrieved 5 chunks for query
2026-05-08T20:53:38 [INFO] sa_resident_agent.llm.utsa_client — LLM call: model=llama-3.3-70b tokens=312
2026-05-08T20:53:39 [INFO] sa_resident_agent.api.routes — Response generated: 1198ms
2026-05-08T20:53:39 [INFO] sa_resident_agent.api.app — RESPONSE id=a1b2c3d4 status=200 duration=1243ms
```

## Log Levels

| Level | When Used |
|---|---|
| INFO | Normal request/response lifecycle, startup, shutdown |
| WARNING | Degraded state (LLM slow, cache miss, partial results) |
| ERROR | Failed requests, connection errors, validation failures |
| CRITICAL | System unable to start, ChromaDB empty, LLM unreachable |

## Log Locations

| Service | View command |
|---|---|
| Backend API | `docker compose logs -f api` |
| PostgreSQL | `docker compose logs -f db` |
| Redis | `docker compose logs -f redis` |
| Crawler/Agent | Terminal running `python server.py` |

## Environment Variable

Set `LOG_LEVEL` in `.env` to control verbosity:
```
LOG_LEVEL=INFO    # default
LOG_LEVEL=DEBUG   # verbose (includes retriever chunk content)
LOG_LEVEL=WARNING # quiet (errors only)
```
