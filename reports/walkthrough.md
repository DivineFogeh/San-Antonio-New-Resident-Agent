# Manual Walkthrough Report

**Project:** SA New Resident Agent  
**Grader:** TA  
**Date:** _______________  
**Commit SHA:** _______________

---

## Setup

- [ ] Backend started: `cd backend && docker compose up -d`
- [ ] Crawler started: `cd crawler && python server.py --host 0.0.0.0 --port 8001`
- [ ] Frontend started: `cd frontend && python -m http.server 3000`
- [ ] All services healthy: `curl http://localhost:8000/` returns `{"status": "ok"}`

---

## Story Results

| Story | Title | Result | Observation |
|---|---|---|---|
| US-01 | Ask about CPS Energy rates | ☐ PASS / ☐ FAIL | |
| US-02 | Ask about SAWS water service requirements | ☐ PASS / ☐ FAIL | |
| US-03 | Ask about City of San Antonio permits | ☐ PASS / ☐ FAIL | |
| US-04 | Get form field guidance | ☐ PASS / ☐ FAIL | |
| US-05 | Check setup progress checklist | ☐ PASS / ☐ FAIL | |
| US-06 | Reset session and start over | ☐ PASS / ☐ FAIL | |
| US-07 | Handle unanswerable question gracefully | ☐ PASS / ☐ FAIL | |
| US-08 | Handle empty message input | ☐ PASS / ☐ FAIL | |
| US-09 | Create user session and seed checklist | ☐ PASS / ☐ FAIL | |
| US-10 | Mark checklist item complete | ☐ PASS / ☐ FAIL | |
| US-11 | Complete CPS Energy enrollment form | ☐ PASS / ☐ FAIL | |
| US-12 | Complete SAWS water enrollment form | ☐ PASS / ☐ FAIL | |

---

## Score

- Stories passed: ___ / 12
- Score: (___ / 12) × 20 = ___

---

## Notes

_______________________________________________
