# SA Resident Agent — User Stories

**Version:** 1.0  
**Project:** CS 6263 NLP and Agentic AI — Final Project  
**Scope:** Web Crawling / Knowledge Base / AI Agent Layer

> **TA Note:** All stories are exercisable against the running system via `docker compose up`.  
> The agent API is available at `http://localhost:8000`.  
> A Swagger UI is available at `http://localhost:8000/docs`.  
> Screenshots for each story are in `docs/assets/stories/`.

---

## Story Index

| ID | Title | Pillar |
|---|---|---|
| US-01 | Ask about CPS Energy rates | Core Q&A |
| US-02 | Ask about SAWS water service requirements | Core Q&A |
| US-03 | Ask about City of San Antonio permits | Core Q&A |
| US-04 | Get form field guidance | Form Help |
| US-05 | Check setup progress checklist | Status |
| US-06 | Reset session and start over | Session Management |
| US-07 | Handle unanswerable question gracefully | Error Path |
| US-08 | Handle empty message input | Error Path |

---

## US-01 — Ask about CPS Energy rates

**As a** new resident,  
**I want to** ask the agent about CPS Energy electricity rates,  
**So that** I understand what I will be charged before enrolling.

### Acceptance Criteria

- **Given** a valid session ID and the ChromaDB index is populated with CPS Energy content  
- **When** the user sends the message `"What are the current CPS Energy residential rates?"`  
- **Then** the agent returns a reply that references rate information sourced from the CPS Energy index, with at least one `sources` entry where `provider` is `CPS_ENERGY`, and `intent` is `QUESTION`

### Manual Walkthrough Steps

1. Open `http://localhost:8000/docs` in a browser.
2. Expand `POST /chat`.
3. Click **Try it out**.
4. Enter the following request body:
   ```json
   {
     "session_id": "test-us01",
     "message": "What are the current CPS Energy residential rates?"
   }
   ```
5. Click **Execute**.
6. Verify the response has HTTP status `200`.
7. Verify `intent` equals `"QUESTION"`.
8. Verify `reply` contains rate-related information (mentions kWh, dollars, or pricing).
9. Verify `sources` contains at least one entry with `"provider": "CPS_ENERGY"`.
10. Verify `checklist.cps_energy` is `"IN_PROGRESS"` or `"NOT_STARTED"` (not changed by a question alone).

**Expected screenshot:** `docs/assets/stories/us_01_expected.png`

---

## US-02 — Ask about SAWS water service requirements

**As a** new resident,  
**I want to** ask what documents I need to sign up for SAWS water service,  
**So that** I can gather the right paperwork before starting the process.

### Acceptance Criteria

- **Given** a valid session ID and the ChromaDB index is populated with SAWS content  
- **When** the user sends `"What documents do I need to sign up for SAWS?"`  
- **Then** the agent returns a reply that mentions at least one required document, with at least one `sources` entry where `provider` is `SAWS`, and `intent` is `QUESTION`

### Manual Walkthrough Steps

1. Open `http://localhost:8000/docs` in a browser.
2. Expand `POST /chat`.
3. Click **Try it out**.
4. Enter:
   ```json
   {
     "session_id": "test-us02",
     "message": "What documents do I need to sign up for SAWS?"
   }
   ```
5. Click **Execute**.
6. Verify HTTP status `200`.
7. Verify `intent` equals `"QUESTION"`.
8. Verify `reply` mentions at least one document type (e.g., ID, lease, proof of address).
9. Verify `sources` contains at least one entry with `"provider": "SAWS"`.

**Expected screenshot:** `docs/assets/stories/us_02_expected.png`

---

## US-03 — Ask about City of San Antonio permits

**As a** new resident,  
**I want to** ask about City of San Antonio registration or permit requirements,  
**So that** I know what city-level steps I need to complete.

### Acceptance Criteria

- **Given** a valid session ID and the ChromaDB index is populated with City of SA content  
- **When** the user sends `"How do I register with the City of San Antonio as a new resident?"`  
- **Then** the agent returns a reply with relevant city registration information, at least one source with `provider` `CITY_SA`, and `intent` `QUESTION`

### Manual Walkthrough Steps

1. Open `http://localhost:8000/docs`.
2. Expand `POST /chat`, click **Try it out**.
3. Enter:
   ```json
   {
     "session_id": "test-us03",
     "message": "How do I register with the City of San Antonio as a new resident?"
   }
   ```
4. Click **Execute**.
5. Verify HTTP status `200`.
6. Verify `intent` equals `"QUESTION"`.
7. Verify `reply` contains city registration guidance.
8. Verify `sources` contains at least one entry with `"provider": "CITY_SA"`.

**Expected screenshot:** `docs/assets/stories/us_03_expected.png`

---

## US-04 — Get form field guidance

**As a** new resident filling out the CPS Energy enrollment form,  
**I want to** ask the agent what to enter in the "Service Address" field,  
**So that** I don't make an error that delays my enrollment.

### Acceptance Criteria

- **Given** a valid session ID  
- **When** the user sends `"What should I enter for the service address field on the CPS Energy form?"`  
- **Then** the agent returns a reply with field-level guidance, `intent` is `FORM_HELP`, and `checklist.cps_energy` advances to at least `IN_PROGRESS`

### Manual Walkthrough Steps

1. Open `http://localhost:8000/docs`.
2. Expand `POST /chat`, click **Try it out**.
3. Enter:
   ```json
   {
     "session_id": "test-us04",
     "message": "What should I enter for the service address field on the CPS Energy form?"
   }
   ```
4. Click **Execute**.
5. Verify HTTP status `200`.
6. Verify `intent` equals `"FORM_HELP"`.
7. Verify `reply` gives guidance specific to an address field (format, example, or requirement).
8. Verify `checklist.cps_energy` is `"IN_PROGRESS"` or `"COMPLETE"`.

**Expected screenshot:** `docs/assets/stories/us_04_expected.png`

---

## US-05 — Check setup progress checklist

**As a** new resident who has already asked questions about CPS Energy,  
**I want to** check which services I have completed and which are still pending,  
**So that** I know what's left to do.

### Acceptance Criteria

- **Given** a session that has previously interacted with the agent (at least one prior `/chat` call)  
- **When** the user calls `GET /status/{session_id}`  
- **Then** the response contains a `checklist` with keys `cps_energy`, `saws`, `city_sa`, each with a valid status value, and a `turn_count` greater than 0

### Manual Walkthrough Steps

1. First, send at least one message using `POST /chat` with `session_id: "test-us05"` (e.g., any message from US-01).
2. Open `http://localhost:8000/docs`.
3. Expand `GET /status/{session_id}`.
4. Click **Try it out**.
5. Enter `session_id`: `test-us05`.
6. Click **Execute**.
7. Verify HTTP status `200`.
8. Verify `checklist` contains keys `cps_energy`, `saws`, `city_sa`.
9. Verify each value is one of `NOT_STARTED`, `IN_PROGRESS`, or `COMPLETE`.
10. Verify `turn_count` is `1` or greater.

**Expected screenshot:** `docs/assets/stories/us_05_expected.png`

---

## US-06 — Reset session and start over

**As a** new resident who wants to restart the setup process,  
**I want to** reset my session,  
**So that** my checklist and conversation history are cleared.

### Acceptance Criteria

- **Given** a session with existing conversation history and checklist state  
- **When** `POST /reset` is called with that session ID  
- **Then** the response has `reset: true`, and a subsequent `GET /status/{session_id}` shows all checklist items as `NOT_STARTED` and `turn_count` as `0`

### Manual Walkthrough Steps

1. Send at least one `/chat` message with `session_id: "test-us06"`.
2. Confirm session has state via `GET /status/test-us06` (turn_count > 0).
3. Open `http://localhost:8000/docs`.
4. Expand `POST /reset`, click **Try it out**.
5. Enter:
   ```json
   { "session_id": "test-us06" }
   ```
6. Click **Execute**.
7. Verify HTTP status `200` and `"reset": true` in response.
8. Call `GET /status/test-us06` again.
9. Verify all three checklist values are `"NOT_STARTED"`.
10. Verify `turn_count` is `0`.

**Expected screenshot:** `docs/assets/stories/us_06_expected.png`

---

## US-07 — Handle unanswerable question gracefully *(Error Path)*

**As a** new resident who asks a question outside the agent's knowledge,  
**I want to** receive a clear, honest response instead of a hallucinated answer,  
**So that** I am not misled by incorrect information.

### Acceptance Criteria

- **Given** a valid session ID  
- **When** the user sends a question with no relevant content in the index, e.g. `"What is the capital of France?"`  
- **Then** the agent returns HTTP `200`, `intent` is `QUESTION`, `sources` is empty or minimal, and `reply` indicates the information is not available (does not fabricate an answer)

### Manual Walkthrough Steps

1. Open `http://localhost:8000/docs`.
2. Expand `POST /chat`, click **Try it out**.
3. Enter:
   ```json
   {
     "session_id": "test-us07",
     "message": "What is the capital of France?"
   }
   ```
4. Click **Execute**.
5. Verify HTTP status `200`.
6. Verify `reply` does NOT contain "Paris" presented as a factual answer in the context of utility setup.
7. Verify `reply` contains a graceful deflection (e.g., "I don't have that information" or directs user to a service website).
8. Verify `sources` is empty or contains no high-confidence results.

**Expected screenshot:** `docs/assets/stories/us_07_expected.png`

---

## US-08 — Handle empty message input *(Error Path)*

**As a** developer or user who accidentally submits an empty message,  
**I want to** receive a validation error instead of a crash or hallucinated response,  
**So that** the system behaves predictably under bad input.

### Acceptance Criteria

- **Given** a valid session ID  
- **When** `POST /chat` is called with `message: ""`  
- **Then** the API returns HTTP `422` with a validation error body

### Manual Walkthrough Steps

1. Open `http://localhost:8000/docs`.
2. Expand `POST /chat`, click **Try it out**.
3. Enter:
   ```json
   {
     "session_id": "test-us08",
     "message": ""
   }
   ```
4. Click **Execute**.
5. Verify HTTP status `422`.
6. Verify the response body contains an error message referencing the `message` field.
7. Verify the system does not return a `200` with a reply.

**Expected screenshot:** `docs/assets/stories/us_08_expected.png`