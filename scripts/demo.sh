#!/bin/bash
# scripts/demo.sh
# Exercises every user story end-to-end against the running system.
# Usage: bash scripts/demo.sh
# Prerequisites: backend running at localhost:8000, crawler at localhost:8001

set -e

BACKEND="http://localhost:8000"
PASS=0
FAIL=0

check() {
    local story="$1"
    local desc="$2"
    local cmd="$3"
    echo -n "  [$story] $desc ... "
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
echo "SA New Resident Agent — Demo Script"
echo "Running all user stories end-to-end"
echo "========================================"
echo ""

# Check backend is up
if ! curl -sf "$BACKEND/" > /dev/null 2>&1; then
    echo "❌ Backend not reachable at $BACKEND"
    echo "   Run: cd backend && docker compose up -d"
    exit 1
fi
echo "✅ Backend is reachable"

# Check crawler is up
if ! curl -sf "http://localhost:8001/health" > /dev/null 2>&1; then
    echo "❌ Crawler not reachable at localhost:8001"
    echo "   Run: cd crawler && python server.py --host 0.0.0.0 --port 8001"
    exit 1
fi
echo "✅ Crawler is reachable"
echo ""

# Create a test user
USER_RESP=$(curl -sf -X POST "$BACKEND/api/user/session" \
    -H "Content-Type: application/json" \
    -d '{"name":"Demo User","email":"demo-script@test.com","address":"123 Main St, San Antonio, TX"}')
USER_ID=$(echo $USER_RESP | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])" 2>/dev/null)
echo "✅ Test user created: $USER_ID"
echo ""

echo "📋 Running user stories..."
echo ""

# US-01: CPS Energy rates
check "US-01" "CPS Energy rates Q&A" \
    "curl -sf -X POST '$BACKEND/api/services/agent/chat' \
     -H 'Content-Type: application/json' \
     -d '{\"session_id\":\"demo-us01\",\"message\":\"What are the current CPS Energy residential rates?\"}' \
     | python3 -c \"import sys,json; d=json.load(sys.stdin); assert d['status']=='success'\""

# US-02: SAWS requirements
check "US-02" "SAWS water service requirements" \
    "curl -sf -X POST '$BACKEND/api/services/agent/chat' \
     -H 'Content-Type: application/json' \
     -d '{\"session_id\":\"demo-us02\",\"message\":\"What documents do I need to sign up for SAWS?\"}' \
     | python3 -c \"import sys,json; d=json.load(sys.stdin); assert d['status']=='success'\""

# US-03: City of SA
check "US-03" "City of San Antonio registration" \
    "curl -sf -X POST '$BACKEND/api/services/agent/chat' \
     -H 'Content-Type: application/json' \
     -d '{\"session_id\":\"demo-us03\",\"message\":\"How do I register with the City of San Antonio as a new resident?\"}' \
     | python3 -c \"import sys,json; d=json.load(sys.stdin); assert d['status']=='success'\""

# US-04: Form field guidance
check "US-04" "Form field guidance" \
    "curl -sf -X POST '$BACKEND/api/services/agent/chat' \
     -H 'Content-Type: application/json' \
     -d '{\"session_id\":\"demo-us04\",\"message\":\"What should I enter for the service address field on the CPS Energy form?\"}' \
     | python3 -c \"import sys,json; d=json.load(sys.stdin); assert d['status']=='success'\""

# US-05: Checklist
check "US-05" "Check setup progress checklist" \
    "curl -sf '$BACKEND/api/checklist/$USER_ID' \
     | python3 -c \"import sys,json; d=json.load(sys.stdin); assert len(d)==9\""

# US-06: Reset session
check "US-06" "Reset session" \
    "curl -sf -X POST '$BACKEND/api/services/agent/reset' \
     -H 'Content-Type: application/json' \
     -d '{\"session_id\":\"demo-us06\"}' \
     | python3 -c \"import sys,json; d=json.load(sys.stdin); assert d['data']['reset']==True\""

# US-07: Unanswerable question
check "US-07" "Handle unanswerable question gracefully" \
    "curl -sf -X POST '$BACKEND/api/services/agent/chat' \
     -H 'Content-Type: application/json' \
     -d '{\"session_id\":\"demo-us07\",\"message\":\"What is the capital of France?\"}' \
     | python3 -c \"import sys,json; d=json.load(sys.stdin); assert d['status']=='success'\""

# US-08: Empty message (expect 422)
check "US-08" "Empty message returns 422" \
    "curl -sf -o /dev/null -w '%{http_code}' -X POST '$BACKEND/api/services/agent/chat' \
     -H 'Content-Type: application/json' \
     -d '{\"session_id\":\"demo-us08\",\"message\":\"\"}' | grep -q 422"

# US-09: Create user session
check "US-09" "Create user session and seed checklist" \
    "curl -sf -X POST '$BACKEND/api/user/session' \
     -H 'Content-Type: application/json' \
     -d '{\"name\":\"Test\",\"email\":\"test-us09@test.com\",\"address\":\"456 Oak St\"}' \
     | python3 -c \"import sys,json; d=json.load(sys.stdin); assert 'id' in d\""

# US-10: Mark checklist complete
check "US-10" "Mark checklist item complete" \
    "curl -sf -X PATCH '$BACKEND/api/checklist/$USER_ID' \
     -H 'Content-Type: application/json' \
     -d '{\"service\":\"cps\",\"step\":\"account\",\"completed\":true}' \
     | python3 -c \"import sys,json; d=json.load(sys.stdin); assert d['status']=='updated'\""

# US-11: Frontend accessible
check "US-11" "Frontend index.html accessible" \
    "[ -f frontend/index.html ]"

# US-12: Frontend SAWS form exists
check "US-12" "Frontend SAWS form defined" \
    "grep -q 'saws' frontend/index.html"

echo ""
echo "========================================"
echo "Demo Summary: $PASS passed, $FAIL failed"
echo "========================================"

if [ $FAIL -eq 0 ]; then
    echo "✅ All stories passed!"
    exit 0
else
    echo "❌ $FAIL story/stories failed"
    exit 1
fi
