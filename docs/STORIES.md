# SA New Resident Agent — User Stories

**Version:** 1.0
**Project:** CS 6263 NLP and Agentic AI — Final Project
**Team:** Divine Fejiro, Tobi, Kemi Ogunbameru

> **TA Note:** All stories are exercisable against the running system.
> Start both services before testing:
> - Backend: `cd backend && docker compose up -d` → `http://localhost:8000`
> - Crawler/Agent: `cd crawler && python server.py --host 0.0.0.0 --port 8001` → `http://localhost:8001`
> - Swagger UI: `http://localhost:8000/docs` and `http://localhost:8001/docs`

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
| US-09 | Create user session and seed checklist | Backend |
| US-10 | Mark checklist item complete | Backend |
| US-11 | Complete CPS Energy enrollment form | Form Engine |
| US-12 | Complete SAWS water enrollment form | Form Engine |

---

## US-01 — Ask about CPS Energy rates

**As a** new resident,
**I want to** ask the agent about CPS Energy electricity rates,
**So that** I understand what I will be charged before enrolling.

### Acceptance Criteria

- **Given** the backend is running and the ChromaDB index is populated
- **When** the user sends `"What are the current CPS Energy residential rates?"` to `POST /api/services/agent/chat`
- **Then** the response has HTTP 200, `status` is `"success"`, and `data.reply` contains rate-related information

### Manual Walkthrough Steps

1. Open `http://localhost:8000/docs` in a browser.
2. Expand `POST /api/services/agent/chat`.
3. Click **Try it out**.
4. Enter:
   ```json
   { "session_id": "test-us01", "message": "What are the current CPS Energy residential rates?" }
   ```
5. Click **Execute**.
6. Verify HTTP status `200`.
7. Verify `status` equals `"success"`.
8. Verify `data.reply` mentions rates, pricing, or kWh.
9. Verify `data.intent` equals `"QUESTION"`.

**Expected screenshot:** `docs/assets/stories/us_01_expected.png`

---

## US-02 — Ask about SAWS water service requirements

**As a** new resident,
**I want to** ask what documents I need to sign up for SAWS water service,
**So that** I can gather the right paperwork before starting.

### Acceptance Criteria

- **Given** the backend is running and the ChromaDB index is populated
- **When** the user sends `"What documents do I need to sign up for SAWS?"` to `POST /api/services/agent/chat`
- **Then** the response has HTTP 200 and `data.reply` mentions at least one required document

### Manual Walkthrough Steps

1. Open `http://localhost:8000/docs`.
2. Expand `POST /api/services/agent/chat`, click **Try it out**.
3. Enter:
   ```json
   { "session_id": "test-us02", "message": "What documents do I need to sign up for SAWS?" }
   ```
4. Click **Execute**.
5. Verify HTTP status `200`.
6. Verify `data.reply` mentions at least one document (ID, lease, proof of address).
7. Verify `data.intent` equals `"QUESTION"`.

**Expected screenshot:** `docs/assets/stories/us_02_expected.png`

---

## US-03 — Ask about City of San Antonio permits

**As a** new resident,
**I want to** ask about City of San Antonio registration requirements,
**So that** I know what city-level steps I need to complete.

### Acceptance Criteria

- **Given** the backend is running and the ChromaDB index is populated
- **When** the user sends `"How do I register with the City of San Antonio as a new resident?"`
- **Then** the response has HTTP 200 and `data.reply` contains city registration guidance

### Manual Walkthrough Steps

1. Open `http://localhost:8000/docs`.
2. Expand `POST /api/services/agent/chat`, click **Try it out**.
3. Enter:
   ```json
   { "session_id": "test-us03", "message": "How do I register with the City of San Antonio as a new resident?" }
   ```
4. Click **Execute**.
5. Verify HTTP status `200`.
6. Verify `data.reply` contains city registration guidance.
7. Verify `data.intent` equals `"QUESTION"`.

**Expected screenshot:** `docs/assets/stories/us_03_expected.png`

---

## US-04 — Get form field guidance

**As a** new resident filling out the CPS Energy enrollment form,
**I want to** ask the agent what to enter in the "Service Address" field,
**So that** I don't make an error that delays my enrollment.

### Acceptance Criteria

- **Given** the backend is running
- **When** the user sends `"What should I enter for the service address field on the CPS Energy form?"`
- **Then** HTTP 200, `data.intent` is `"FORM_HELP"`, and `data.reply` gives address field guidance

### Manual Walkthrough Steps

1. Open `http://localhost:8000/docs`.
2. Expand `POST /api/services/agent/chat`, click **Try it out**.
3. Enter:
   ```json
   { "session_id": "test-us04", "message": "What should I enter for the service address field on the CPS Energy form?" }
   ```
4. Click **Execute**.
5. Verify HTTP status `200`.
6. Verify `data.intent` equals `"FORM_HELP"`.
7. Verify `data.reply` gives guidance on address format or requirements.

**Expected screenshot:** `docs/assets/stories/us_04_expected.png`

---

## US-05 — Check setup progress checklist

**As a** new resident who has already asked questions,
**I want to** check which services I have completed,
**So that** I know what's left to do.

### Acceptance Criteria

- **Given** a user session exists in the backend
- **When** `GET /api/checklist/{user_id}` is called
- **Then** HTTP 200 and a list of checklist items with service, step, and completed fields

### Manual Walkthrough Steps

1. First create a user via `POST /api/user/session` with name, email, address.
2. Copy the `id` from the response.
3. Expand `GET /api/checklist/{user_id}`, click **Try it out**.
4. Enter the user `id`.
5. Click **Execute**.
6. Verify HTTP status `200`.
7. Verify response contains 9 checklist items (3 services × 3 steps).
8. Verify each item has `service`, `step`, and `completed` fields.

**Expected screenshot:** `docs/assets/stories/us_05_expected.png`

---

## US-06 — Reset session and start over

**As a** new resident who wants to restart the setup process,
**I want to** reset my AI agent session,
**So that** my conversation history is cleared.

### Acceptance Criteria

- **Given** a session with existing conversation history
- **When** `POST /api/services/agent/reset` is called with that session ID
- **Then** HTTP 200 and `data.reset` is `true`

### Manual Walkthrough Steps

1. Send at least one message via `POST /api/services/agent/chat` with `session_id: "test-us06"`.
2. Expand `POST /api/services/agent/reset`, click **Try it out**.
3. Enter:
   ```json
   { "session_id": "test-us06" }
   ```
4. Click **Execute**.
5. Verify HTTP status `200`.
6. Verify `data.reset` equals `true`.

**Expected screenshot:** `docs/assets/stories/us_06_expected.png`

---

## US-07 — Handle unanswerable question gracefully *(Error Path)*

**As a** new resident who asks a question outside the agent's knowledge,
**I want to** receive an honest response instead of a hallucinated answer,
**So that** I am not misled by incorrect information.

### Acceptance Criteria

- **Given** the backend is running
- **When** the user sends `"What is the capital of France?"`
- **Then** HTTP 200, and `data.reply` indicates the information is not available (does not fabricate utility-related answer)

### Manual Walkthrough Steps

1. Open `http://localhost:8000/docs`.
2. Expand `POST /api/services/agent/chat`, click **Try it out**.
3. Enter:
   ```json
   { "session_id": "test-us07", "message": "What is the capital of France?" }
   ```
4. Click **Execute**.
5. Verify HTTP status `200`.
6. Verify `data.reply` contains a graceful deflection or "I don't have that information".
7. Verify `data.reply` does NOT present Paris as a utility-related answer.

**Expected screenshot:** `docs/assets/stories/us_07_expected.png`

---

## US-08 — Handle empty message input *(Error Path)*

**As a** developer who accidentally submits an empty message,
**I want to** receive a validation error,
**So that** the system behaves predictably under bad input.

### Acceptance Criteria

- **Given** the backend is running
- **When** `POST /api/services/agent/chat` is called with an empty `message`
- **Then** HTTP 422 with a validation error body

### Manual Walkthrough Steps

1. Open `http://localhost:8000/docs`.
2. Expand `POST /api/services/agent/chat`, click **Try it out**.
3. Enter:
   ```json
   { "session_id": "test-us08", "message": "" }
   ```
4. Click **Execute**.
5. Verify HTTP status `422`.
6. Verify response body contains a validation error.

**Expected screenshot:** `docs/assets/stories/us_08_expected.png`

---

## US-09 — Create user session and seed checklist *(Backend)*

**As a** new resident opening the app for the first time,
**I want to** create a session that tracks my progress,
**So that** the system remembers what I have completed.

### Acceptance Criteria

- **Given** the backend is running
- **When** `POST /api/user/session` is called with name, email, and address
- **Then** HTTP 200, a user ID is returned, and 9 checklist items are seeded

### Manual Walkthrough Steps

1. Open `http://localhost:8000/docs`.
2. Expand `POST /api/user/session`, click **Try it out**.
3. Enter:
   ```json
   { "name": "Maria Garcia", "email": "maria@test.com", "address": "123 Main St, San Antonio, TX" }
   ```
4. Click **Execute**.
5. Verify HTTP status `200`.
6. Verify response contains `id`, `name`, `email`, `created_at`.
7. Call `GET /api/checklist/{id}` with the returned ID.
8. Verify 9 checklist items are returned, all `completed: false`.

**Expected screenshot:** `docs/assets/stories/us_09_expected.png`

---

## US-10 — Mark checklist item complete *(Backend)*

**As a** new resident who has finished setting up CPS Energy,
**I want to** mark that step as complete,
**So that** my progress dashboard updates.

### Acceptance Criteria

- **Given** a user session exists
- **When** `PATCH /api/checklist/{user_id}` is called with service, step, and completed=true
- **Then** HTTP 200 and the item is marked complete

### Manual Walkthrough Steps

1. Create a user via `POST /api/user/session`, copy the ID.
2. Expand `PATCH /api/checklist/{user_id}`, click **Try it out**.
3. Enter the user ID and body:
   ```json
   { "service": "cps", "step": "account", "completed": true }
   ```
4. Click **Execute**.
5. Verify HTTP status `200`.
6. Call `GET /api/checklist/{user_id}` again.
7. Verify the `cps` / `account` item now has `completed: true`.

**Expected screenshot:** `docs/assets/stories/us_10_expected.png`

---

## US-11 — Complete CPS Energy enrollment form *(Form Engine)*

**As a** new resident,
**I want to** fill out the CPS Energy enrollment form step by step,
**So that** my electric service is set up.

### Acceptance Criteria

- **Given** the frontend is open and backend is running
- **When** the user fills out all 3 steps of the CPS Energy form
- **Then** the form is submitted to the backend and CPS shows as completed in the dashboard

### Manual Walkthrough Steps

1. cd frontend && python -m http.server 3000
   Open http://localhost:3000 in a browser.
2. Verify the header shows "Backend connected" in green.
3. Click **CPS Energy** in the left sidebar.
4. Fill in Step 1 (Personal Information) — First Name, Last Name, last 4 of SSN, Date of Birth.
5. Click **Next →**.
6. Fill in Step 2 (Service Address) — a San Antonio address and 78201 ZIP code.
7. Click **Next →**.
8. Fill in Step 3 (Contact & Plan) — email, phone, select a rate plan.
9. Click **Submit ✓**.
10. Verify the success screen appears: "🎉 CPS Energy Submitted!"
11. Verify the sidebar badge for CPS Energy changes to "Done".
12. Verify progress bar updates to 33%.

**Expected screenshot:** `docs/assets/stories/us_11_expected.png`

---

## US-12 — Complete SAWS water enrollment form *(Form Engine)*

**As a** new resident,
**I want to** fill out the SAWS water enrollment form,
**So that** my water service is set up.

### Acceptance Criteria

- **Given** the frontend is open and backend is running
- **When** the user fills out all 3 steps of the SAWS form
- **Then** the form is submitted to the backend and SAWS shows as completed in the dashboard

### Manual Walkthrough Steps

1. cd frontend && python -m http.server 3000
   Open http://localhost:3000 in a browser.
2. Click **SAWS Water** in the left sidebar.
3. Fill in Step 1 (Account Holder) — First Name, Last Name, ID Type, ID Number.
4. Click **Next →**.
5. Fill in Step 2 (Service Address) — a San Antonio address and 78201 ZIP code.
6. Click **Next →**.
7. Fill in Step 3 (Billing Preferences) — email, phone, AutoPay preference.
8. Click **Submit ✓**.
9. Verify the success screen appears: "🎉 SAWS Water Submitted!"
10. Verify the sidebar badge for SAWS Water changes to "Done".
11. Verify progress bar updates to 66%.

**Expected screenshot:** `docs/assets/stories/us_12_expected.png`
