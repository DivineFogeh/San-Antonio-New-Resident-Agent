# Usage Guide

## Overview

This guide covers how to use the SA New Resident Agent for each user story. Start both services before following any story:

```bash
# Terminal 1 — Backend
cd backend && docker compose up -d

# Terminal 2 — Crawler/AI Agent
cd crawler && python server.py --host 0.0.0.0 --port 8001
```

Then open http://localhost:8000/docs for the backend Swagger UI.

---

## US-01 — Ask about CPS Energy rates

Navigate to `POST /api/services/agent/chat` in the Swagger UI. Send:
```json
{ "session_id": "my-session", "message": "What are the current CPS Energy residential rates?" }
```
The response will include rate information sourced from the CPS Energy knowledge base.

---

## US-02 — Ask about SAWS water service requirements

Navigate to `POST /api/services/agent/chat`. Send:
```json
{ "session_id": "my-session", "message": "What documents do I need to sign up for SAWS?" }
```
The response will list required documents for SAWS water service enrollment.

---

## US-03 — Ask about City of San Antonio permits

Navigate to `POST /api/services/agent/chat`. Send:
```json
{ "session_id": "my-session", "message": "How do I register with the City of San Antonio as a new resident?" }
```
The response will provide city registration guidance.

---

## US-04 — Get form field guidance

Navigate to `POST /api/services/agent/chat`. Send:
```json
{ "session_id": "my-session", "message": "What should I enter for the service address field on the CPS Energy form?" }
```
The agent will return field-level guidance with the intent `FORM_HELP`.

---

## US-05 — Check setup progress checklist

First create a user via `POST /api/user/session`. Then navigate to `GET /api/checklist/{user_id}` and enter your user ID. The response shows all 9 checklist items (3 services × 3 steps) with their completion status.

---

## US-06 — Reset session and start over

Navigate to `POST /api/services/agent/reset`. Send:
```json
{ "session_id": "my-session" }
```
This clears conversation history and resets the AI agent's checklist for that session.

---

## US-07 — Handle unanswerable question gracefully

Navigate to `POST /api/services/agent/chat`. Send:
```json
{ "session_id": "my-session", "message": "What is the capital of France?" }
```
The agent will respond with a graceful deflection rather than fabricating an answer.

---

## US-08 — Handle empty message input

Navigate to `POST /api/services/agent/chat`. Send:
```json
{ "session_id": "my-session", "message": "" }
```
The API returns HTTP 422 with a validation error — it does not crash or hallucinate.

---

## US-09 — Create user session and seed checklist

Navigate to `POST /api/user/session`. Send:
```json
{ "name": "Maria Garcia", "email": "maria@test.com", "address": "123 Main St, San Antonio, TX" }
```
A user ID is returned and 9 checklist items are automatically seeded in PostgreSQL.

---

## US-10 — Mark checklist item complete

First create a user (US-09). Then navigate to `PATCH /api/checklist/{user_id}`. Send:
```json
{ "service": "cps", "step": "account", "completed": true }
```
The checklist item is updated in PostgreSQL and the Redis cache is invalidated.

---

## US-11 — Complete CPS Energy enrollment form

Open `frontend/sa_new_resident_agent.py` in Jupyter. Run all cells. In Cell 9 (CPS Energy Form), fill out all 3 steps and click Submit. The form data is sent to the backend and the progress dashboard updates.

---

## US-12 — Complete SAWS water enrollment form

In Cell 10 (SAWS Water Form), fill out all 3 steps and click Submit. The form data is sent to the backend and SAWS shows as Complete in the dashboard.
