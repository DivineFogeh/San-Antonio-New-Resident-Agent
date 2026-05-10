#!/bin/bash
# scripts/preflight.sh
# Runs every automated check the TA will run.
# If preflight passes locally, your automated grade passes.
# Usage: bash scripts/preflight.sh

set -e

PASS=0
FAIL=0
TOTAL=0

check() {
    local name="$1"
    local cmd="$2"
    TOTAL=$((TOTAL + 1))
    echo -n "  [$TOTAL] $name ... "
    if eval "$cmd" > /dev/null 2>&1; then
        echo "✅ PASS"
        PASS=$((PASS + 1))
    else
        echo "❌ FAIL"
        FAIL=$((FAIL + 1))
    fi
}

echo ""
echo "========================================"
echo "SA New Resident Agent — Preflight Check"
echo "========================================"
echo ""

# ── Phase 1: Required files ───────────────────────────────────────
echo "📁 Phase 1: Required artifacts"
check "docs/SPEC.md exists"              "[ -f docs/SPEC.md ]"
check "docs/STORIES.md exists"           "[ -f docs/STORIES.md ]"
check "docs/REPRODUCE.md exists"         "[ -f docs/REPRODUCE.md ]"
check "docs/DATA.md exists"              "[ -f docs/DATA.md ]"
check "docs/MODELS.md exists"            "[ -f docs/MODELS.md ]"
check "docs/MODEL_CARD.md exists"        "[ -f docs/MODEL_CARD.md ]"
check "docs/LOGGING.md exists"           "[ -f docs/LOGGING.md ]"
check "docs/usage.md exists"             "[ -f docs/usage.md ]"
check "docs/diagrams/architecture.png"   "[ -f docs/diagrams/architecture.png ]"
check "docs/assets/demo.mp4 exists"      "[ -f docs/assets/demo.mp4 ]"
check "grading/traceability.yaml"        "[ -f grading/traceability.yaml ]"
check "grading/manifest.yaml"            "[ -f grading/manifest.yaml ]"
check "CONTRIBUTIONS.md exists"          "[ -f CONTRIBUTIONS.md ]"
check "Makefile exists"                  "[ -f Makefile ]"
check "reports/git_contributions.txt"    "[ -f reports/git_contributions.txt ]"
check "reports/walkthrough.md"           "[ -f reports/walkthrough.md ]"
check "scripts/regenerate.sh"            "[ -f scripts/regenerate.sh ]"
check "scripts/regenerate_prompt.md"     "[ -f scripts/regenerate_prompt.md ]"
check "backend/Dockerfile"               "[ -f backend/Dockerfile ]"
check "backend/docker-compose.yml"       "[ -f backend/docker-compose.yml ]"
check "backend/.env.example"             "[ -f backend/.env.example ]"
check "backend/requirements.txt"         "[ -f backend/requirements.txt ]"
check "crawler/requirements.txt"         "[ -f crawler/requirements.txt ]"
check "frontend/index.html"              "[ -f frontend/index.html ]"
check "tests/load/locustfile.py"         "[ -f crawler/tests/load/locustfile.py ]"
check "docs/benchmarks.md"              "[ -f docs/benchmarks.md ]"

echo ""
echo "📸 Phase 2: Story screenshots"
for i in $(seq -w 1 12); do
    check "us_${i}_expected.png" "[ -f docs/assets/stories/us_${i}_expected.png ]"
done

echo ""
echo "🧪 Phase 3: Tests"
if [ -d "crawler" ]; then
    check "pytest available" "cd crawler && python -m pytest --version"
    check "crawler tests pass" "cd crawler && pip install -e . -q && python -m pytest tests/ -q --tb=no"
else
    echo "  [SKIP] crawler/ not found"
fi

echo ""
echo "🐳 Phase 4: Docker"
check "docker available"         "docker --version"
check "docker compose available" "docker compose version"
check "backend image builds"     "cd backend && docker compose build --quiet"

echo ""
echo "========================================"
echo "Preflight Summary: $PASS passed, $FAIL failed out of $TOTAL checks"
echo "========================================"

if [ $FAIL -eq 0 ]; then
    echo "✅ All checks passed! Ready to submit."
    exit 0
else
    echo "❌ $FAIL check(s) failed. Fix before submitting."
    exit 1
fi
