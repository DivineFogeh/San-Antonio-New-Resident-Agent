# Makefile — SA New Resident Agent
# Usage: make <target>

.PHONY: help reproduce test lint serve clean preflight

help:
	@echo "SA New Resident Agent — Available targets:"
	@echo ""
	@echo "  make reproduce     Rebuild Docker, build index, run all tests"
	@echo "  make test          Run all tests with coverage"
	@echo "  make lint          Run ruff linter and type checks"
	@echo "  make serve         Start backend + crawler servers"
	@echo "  make loadtest      Run load test against live system"
	@echo "  make preflight     Run all automated checks (what TA runs)"
	@echo "  make clean         Remove generated files and containers"

# ── Reproduce ────────────────────────────────────────────────────────────────
reproduce:
	@echo "=== Step 1: Start backend ==="
	cd backend && docker compose up -d --build
	@echo "=== Step 2: Build ChromaDB index ==="
	cd crawler && pip install -r requirements.txt -q && python main.py
	@echo "=== Step 3: Run tests ==="
	$(MAKE) test
	@echo "=== Reproduce complete ==="

# ── Test ─────────────────────────────────────────────────────────────────────
test:
	cd crawler && pytest tests/ \
		--cov=sa_resident_agent \
		--cov-report=xml:../reports/coverage.xml \
		--cov-report=html:../reports/coverage_html \
		--cov-fail-under=70 \
		--junit-xml=../reports/unit.xml \
		-v

# ── Lint ─────────────────────────────────────────────────────────────────────
lint:
	@echo "=== Running ruff ==="
	cd crawler && ruff check sa_resident_agent/ || true
	@echo "=== Running pip-audit ==="
	pip-audit -r crawler/requirements.txt -o reports/security.txt || true
	@echo "=== Lint complete ==="

# ── Serve ────────────────────────────────────────────────────────────────────
serve:
	@echo "Starting backend..."
	cd backend && docker compose up -d
	@echo "Starting crawler/AI agent on port 8001..."
	cd crawler && python server.py --host 0.0.0.0 --port 8001

# ── Load Test ────────────────────────────────────────────────────────────────
loadtest:
	@echo "Running load test..."
	cd crawler && locust -f tests/load/locustfile.py \
		--headless \
		--users 20 \
		--spawn-rate 5 \
		--run-time 60s \
		--host http://localhost:8001 \
		--html reports/loadtest.html \
		--json > reports/benchmarks.json || true

# ── Preflight ────────────────────────────────────────────────────────────────
preflight:
	@echo "=== Running preflight checks ==="
	$(MAKE) lint
	$(MAKE) test
	bash scripts/regenerate.sh
	@echo "=== Preflight complete ==="

# ── Download Data ────────────────────────────────────────────────────────────
download-data:
	cd crawler && python main.py --providers CPS_ENERGY SAWS CITY_SA

download-models:
	python3 -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
	@echo "Models downloaded."

# ── Clean ────────────────────────────────────────────────────────────────────
clean:
	cd backend && docker compose down -v || true
	rm -rf crawler/data/chroma
	rm -rf reports/
	find . -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	@echo "Clean complete."
