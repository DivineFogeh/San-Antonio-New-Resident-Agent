# Reproduction Guide

## Hardware Profile

| Component | Requirement |
|---|---|
| OS | Windows 10/11, macOS, or Ubuntu 22.04 |
| RAM | 8GB minimum, 16GB recommended |
| Disk | 10GB free (ChromaDB index + Docker images) |
| Network | UTSA WiFi or VPN (required for LLM endpoint) |
| Python | 3.11.x |
| Docker | 24.0+ with Docker Compose v2 |

## Expected Runtime

| Step | Expected Time |
|---|---|
| `docker compose up --build` | 5–10 minutes (first run) |
| `python main.py` (build index) | 10–15 minutes |
| `make test` | 2–5 minutes |

## Expected Metric Values

| Metric | Expected Value | Tolerance |
|---|---|---|
| ChromaDB doc count | 706 chunks | ±50 |
| Test coverage | ≥70% | — |
| User story pass rate | ≥90% | — |
| Load test RPS | ≥10 req/s | — |
| Load test error rate | ≤5% | — |

## Full Reproduction Steps

### Prerequisites

1. Install Docker Desktop: https://www.docker.com/products/docker-desktop/
2. Install Python 3.11: https://www.python.org/downloads/
3. Connect to UTSA WiFi or VPN
4. Clone the repository:
   ```bash
   git clone https://github.com/DivineFogeh/San-Antonio-New-Resident-Agent.git
   cd San-Antonio-New-Resident-Agent
   git checkout develop
   ```

### Step 1 — Start the Backend

```bash
cd backend
cp .env.example .env
docker compose up -d --build
```

Verify: `curl http://localhost:8000/` returns `{"status": "ok"}`

### Step 2 — Build the Knowledge Base (run once)

```bash
cd crawler
pip install -r requirements.txt
playwright install chromium
cp .env.example .env
# Edit .env and add your UTSA_LLM_API_KEY
python main.py
```

Expected output:
```
✅ OK  CPS_ENERGY   pages= 12  chunks= 243
✅ OK  SAWS         pages=  8  chunks= 198
✅ OK  CITY_SA      pages= 11  chunks= 265
All providers indexed successfully.
```

### Step 3 — Start the Crawler/AI Server

```bash
cd crawler
python server.py --host 0.0.0.0 --port 8001
```

Verify: `curl http://localhost:8001/health` returns `{"status": "ok", "chroma_docs": 706}`

### Step 4 — Run Tests

```bash
cd crawler
make test
```

### Step 5 — Run Frontend

```bash
cd frontend
# Open sa_new_resident_agent.py in Jupyter or run locally
jupyter notebook sa_new_resident_agent.py
```

Or open in Google Colab and run all cells.
