"""
agent_test.py

Interactive terminal tester for the full agent pipeline.
Run on UTSA network/VPN after the index is built.

Usage:
    python agent_test.py                    # normal Q&A mode
    python agent_test.py --simulate         # guided signup simulation mode
    python agent_test.py --session my-id
"""

import argparse
import logging
import sys
import uuid

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logging.getLogger("chromadb.telemetry.product.posthog").setLevel(logging.CRITICAL)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("sentence_transformers").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

from sa_resident_agent.agent.agent import Agent
from sa_resident_agent.llm.utsa_client import UTSAClient


CHECKLIST_ICONS = {
    "NOT_STARTED": "⬜",
    "IN_PROGRESS": "🔄",
    "COMPLETE":    "✅",
}

PROVIDER_LABELS = {
    "CPS_ENERGY": "CPS Energy (Electricity)",
    "SAWS":       "SAWS (Water)",
    "CITY_SA":    "City of San Antonio",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="SA Resident Agent — Interactive Test")
    parser.add_argument("--session",     default=None,          help="Session ID (default: random UUID)")
    parser.add_argument("--chroma-path", default="data/chroma", help="ChromaDB path")
    parser.add_argument("--simulate",    action="store_true",   help="Enable guided signup simulation mode")
    return parser.parse_args()


def format_checklist(checklist: dict) -> str:
    lines = []
    for provider, status in checklist.items():
        raw_status = str(status).split(".")[-1]
        icon  = CHECKLIST_ICONS.get(raw_status, "?")
        label = PROVIDER_LABELS.get(provider, provider)
        lines.append(f"  {icon} {label}: {raw_status}")
    return "\n".join(lines)


def print_response(resp):
    print(f"\n{'─'*60}")
    print(f"Intent : {str(resp.intent).split('.')[-1]}")
    print(f"\nChecklist:")
    print(format_checklist(resp.checklist))
    if resp.sources:
        print(f"\nSources: {len(resp.sources)} relevant chunk(s)")
        for i, s in enumerate(resp.sources[:3], 1):
            print(f"  [{i}] {s.provider} | {s.url}")
            print(f"       {s.chunk_preview[:100]}...")
    if resp.error:
        print(f"\n⚠️  Error: {resp.error}")
    print(f"\nAgent: {resp.reply}")
    print(f"{'─'*60}\n")


def main():
    args = parse_args()
    session_id = args.session or str(uuid.uuid4())[:8]

    print("\n" + "="*60)
    print("SA Resident Agent")
    if args.simulate:
        print("MODE: 🎯 Guided Signup Simulation")
    else:
        print("MODE: 💬 Q&A")
    print("="*60)
    print(f"Session ID : {session_id}")
    print(f"ChromaDB   : {args.chroma_path}")
    print("Commands   : 'reset' | 'status' | 'exit'")
    print("="*60)

    if args.simulate:
        print("\n📋 Simulation mode active.")
        print("The agent will walk you through setting up:")
        print("  1. CPS Energy (electricity)")
        print("  2. SAWS (water service)")
        print("  3. City of San Antonio services")
        print("\nJust respond naturally — the agent will guide you.\n")

    llm = UTSAClient()
    print("Checking UTSA LLM endpoint...", end=" ", flush=True)
    if llm.is_reachable():
        print("✅ Reachable\n")
    else:
        print("❌ NOT reachable — make sure you're on UTSA network or VPN\n")

    agent = Agent(
        chroma_path=args.chroma_path,
        llm=llm,
        simulate_mode=args.simulate,
    )

    # In simulate mode, send an opening message automatically
    if args.simulate:
        resp = agent.chat(session_id, "I am a new San Antonio resident and I need to set up my utilities.")
        print_response(resp)

    while True:
        try:
            user_input = input("You > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break

        if not user_input:
            continue

        if user_input.lower() in ("exit", "quit", "q"):
            print("Goodbye.")
            break

        if user_input.lower() == "reset":
            agent.reset(session_id)
            print("✅ Session reset.\n")
            continue

        if user_input.lower() == "status":
            s = agent.status(session_id)
            print(f"\nChecklist:\n{format_checklist(s['checklist'])}")
            print(f"Turns: {s['turn_count']}\n")
            continue

        resp = agent.chat(session_id, user_input)
        print_response(resp)


if __name__ == "__main__":
    main()
