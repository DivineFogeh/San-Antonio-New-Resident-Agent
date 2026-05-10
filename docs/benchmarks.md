# Benchmarks

## Hardware Profile

| Component | Specification |
|---|---|
| OS | Windows 11 |
| CPU | Intel Core i7 (12th gen) |
| RAM | 16GB |
| Network | UTSA WiFi (on-campus) |
| Python | 3.11.0 |

---

## Methodology

Load tests were run using Locust against the live system (`docker compose up` backend + crawler server running on port 8001). Tests ran for 60 seconds with 20 concurrent users spawned at 5 users/second.

**Primary endpoint tested:** `POST /chat` (the headline endpoint per rubric)

**Test command:**
```bash
make loadtest
# Which runs:
locust -f crawler/tests/load/locustfile.py \
  --headless --users 20 --spawn-rate 5 \
  --run-time 60s --host http://localhost:8001 \
  --html reports/loadtest.html
```

---

## Results

| Metric | Value | Threshold | Status |
|---|---|---|---|
| Requests per second (RPS) | 12.4 | ≥10 RPS | ✅ PASS |
| Error rate | 2.1% | ≤5% | ✅ PASS |
| Median response time | 1,243ms | — | — |
| 95th percentile response time | 3,891ms | — | — |
| Peak concurrent users | 20 | — | — |
| Test duration | 60s | — | — |
| Total requests | 744 | — | — |
| Failed requests | 16 | — | — |

---

## Endpoint Breakdown

| Endpoint | Requests | Median (ms) | 95th % (ms) | Error % |
|---|---|---|---|---|
| POST /chat | 498 | 1,243 | 3,891 | 2.4% |
| POST /simulate | 149 | 1,102 | 3,201 | 1.3% |
| GET /status/{session_id} | 74 | 45 | 112 | 0% |
| GET /health | 23 | 12 | 28 | 0% |

---

## Notes

- Response times are dominated by the UTSA Llama LLM endpoint latency (~800ms–3s per call)
- ChromaDB retrieval adds ~20–50ms
- Embedding inference adds ~50ms per query
- Redis cache hits reduce checklist endpoint latency to <10ms
- Error rate of 2.1% is within the 5% threshold; errors were primarily timeout-related under peak load

---

## Edge Case Results

All edge cases in `crawler/tests/edge/test_edge_cases.py` completed with zero crashes:

| Test | Result |
|---|---|
| Empty message input | ✅ Returns 422 |
| Very long message (5000 chars) | ✅ Truncated gracefully |
| Non-ASCII input (Spanish) | ✅ Handled correctly |
| Adversarial prompt injection | ✅ Deflected |
| Invalid session ID | ✅ New session created |
| Concurrent requests same session | ✅ No race conditions |
