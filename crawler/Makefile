# SA Resident Agent — Makefile
# Covers: index build, testing, linting, and server startup.
# Teammate 1 (backend/infra) integrates this into the full project Makefile.

PYTHON      = python
PIP         = pip
CHROMA_PATH = data/chroma
PROVIDERS   = CPS_ENERGY SAWS CITY_SA

.PHONY: all reproduce download-data test lint serve clean help

# ---------------------------------------------------------------------------
# Default
# ---------------------------------------------------------------------------

all: help

# ---------------------------------------------------------------------------
# Reproduce — full crawl + embed + index pipeline
# Run this on a clean machine to rebuild the knowledge base from scratch.
# Called by the TA grading script as: make reproduce
# ---------------------------------------------------------------------------

reproduce: install
	@echo "=== Rebuilding knowledge base from scratch ==="
	$(PYTHON) main.py --rebuild
	@echo "=== Reproduce complete ==="

# Alias used in some grading scripts
download-data: reproduce

# ---------------------------------------------------------------------------
# Install dependencies
# ---------------------------------------------------------------------------

install:
	@echo "=== Installing dependencies ==="
	$(PIP) install -r requirements.txt --quiet
	playwright install chromium
	$(PIP) install -e . --quiet
	@echo "=== Install complete ==="

# ---------------------------------------------------------------------------
# Test — run pytest with coverage
# Fails if coverage drops below 70% (enforced in pytest.ini)
# ---------------------------------------------------------------------------

test: install
	@echo "=== Running test suite ==="
	pytest
	@echo "=== Tests complete ==="

# Run tests without coverage report (faster for dev)
test-fast:
	pytest --no-cov -q

# Run a specific test file
test-file:
	pytest $(FILE) -v

# ---------------------------------------------------------------------------
# Lint — check code quality
# ---------------------------------------------------------------------------

lint: install-lint
	@echo "=== Running linter ==="
	ruff check sa_resident_agent/ tests/
	@echo "=== Lint complete ==="

install-lint:
	$(PIP) install ruff --quiet

# Auto-fix lint issues where possible
lint-fix:
	ruff check sa_resident_agent/ tests/ --fix

# ---------------------------------------------------------------------------
# Security audit
# ---------------------------------------------------------------------------

audit:
	$(PIP) install pip-audit --quiet
	pip-audit -r requirements.txt

# ---------------------------------------------------------------------------
# Serve — start the FastAPI server
# ---------------------------------------------------------------------------

serve:
	$(PYTHON) server.py --host 0.0.0.0 --port 8000

serve-local:
	$(PYTHON) server.py --host 127.0.0.1 --port 8000

# ---------------------------------------------------------------------------
# Preflight — sanity checks before grading
# Verifies index is built, LLM is reachable, tests pass
# ---------------------------------------------------------------------------

preflight:
	@echo "=== Preflight checks ==="
	@$(PYTHON) -c "from sa_resident_agent.knowledge.vector_store import VectorStore; \
		s = VectorStore(); c = s.count(); \
		print(f'ChromaDB: {c} chunks'); \
		exit(0) if c > 0 else exit(1)" || \
		(echo 'ERROR: ChromaDB is empty — run: make reproduce' && exit 1)
	@$(PYTHON) -c "from sa_resident_agent.llm.utsa_client import UTSAClient; \
		ok = UTSAClient().is_reachable(); \
		print(f'LLM reachable: {ok}')"
	@echo "Running tests..."
	@pytest --no-cov -q
	@echo "=== Preflight passed ==="

# ---------------------------------------------------------------------------
# Clean
# ---------------------------------------------------------------------------

clean:
	@echo "=== Cleaning generated files ==="
	rm -rf data/chroma htmlcov .coverage
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "=== Clean complete ==="

clean-index:
	@echo "=== Removing ChromaDB index only ==="
	rm -rf data/chroma
	@echo "Done. Run 'make reproduce' to rebuild."

# ---------------------------------------------------------------------------
# Help
# ---------------------------------------------------------------------------

help:
	@echo ""
	@echo "SA Resident Agent — Available targets:"
	@echo "---------------------------------------"
	@echo "  make reproduce     Crawl all providers and rebuild ChromaDB index"
	@echo "  make test          Run full test suite with coverage (≥70% required)"
	@echo "  make test-fast     Run tests without coverage (faster)"
	@echo "  make lint          Run ruff linter on source and tests"
	@echo "  make lint-fix      Auto-fix lint issues"
	@echo "  make audit         Run pip-audit security check"
	@echo "  make serve         Start FastAPI server on 0.0.0.0:8000"
	@echo "  make serve-local   Start FastAPI server on localhost:8000"
	@echo "  make preflight     Run all sanity checks before grading"
	@echo "  make clean         Remove ChromaDB, coverage, and pycache"
	@echo "  make install       Install all dependencies"
	@echo ""