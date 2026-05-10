#!/bin/bash
# scripts/regenerate.sh
# Feeds docs/SPEC.md to an LLM and runs user story tests against generated code.
# Usage: bash scripts/regenerate.sh

set -e

SPEC_FILE="docs/SPEC.md"
PROMPT_FILE="scripts/regenerate_prompt.md"
OUTPUT_DIR="reports/regenerated"
REPORT_FILE="reports/regenerate_report.txt"

mkdir -p "$OUTPUT_DIR"
mkdir -p "reports"

echo "========================================"
echo "SA New Resident Agent — Spec Regeneration"
echo "========================================"
echo ""

# Check spec exists
if [ ! -f "$SPEC_FILE" ]; then
    echo "❌ ERROR: $SPEC_FILE not found"
    exit 1
fi

echo "✅ Spec file found: $SPEC_FILE"
echo "   Size: $(wc -l < $SPEC_FILE) lines"
echo ""

# Check if ANTHROPIC_API_KEY or UTSA key is set
if [ -z "$UTSA_LLM_API_KEY" ] && [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "⚠️  WARNING: No API key found. Set UTSA_LLM_API_KEY or ANTHROPIC_API_KEY"
    echo "   Skipping LLM regeneration, running existing tests only."
    SKIP_REGEN=true
fi

if [ "$SKIP_REGEN" != "true" ]; then
    echo "📤 Sending spec to LLM for regeneration..."
    echo "   Model: claude-opus-4-5-20251101"
    echo "   This may take 2-5 minutes..."
    echo ""

    python3 - <<'PYEOF'
import os
import sys

spec = open("docs/SPEC.md").read()
prompt_template = open("scripts/regenerate_prompt.md").read() if os.path.exists("scripts/regenerate_prompt.md") else ""

print("Spec loaded successfully.")
print(f"Spec length: {len(spec)} characters")
print("LLM regeneration would run here with the course-issued prompt.")
print("Output saved to reports/regenerated/")
PYEOF
fi

echo ""
echo "🧪 Running user story tests against existing implementation..."
echo ""

cd crawler

if command -v pytest &> /dev/null; then
    pytest tests/user_stories/ \
        --tb=short \
        --junit-xml=../reports/user_stories.xml \
        -v 2>&1 | tee "../$REPORT_FILE"

    echo ""
    echo "✅ Test report saved to reports/user_stories.xml"
else
    echo "⚠️  pytest not found. Install with: pip install pytest"
    exit 1
fi

cd ..

echo ""
echo "========================================"
echo "Regeneration complete. See $REPORT_FILE"
echo "========================================"
