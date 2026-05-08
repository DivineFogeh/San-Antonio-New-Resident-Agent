"""
query.py

Interactive retrieval tester — run this after main.py to verify the
knowledge base is working before building the agent layer.

Usage:
    python query.py
    python query.py --provider CPS_ENERGY
    python query.py --top-k 3
"""

import argparse
import logging
import sys

from sa_resident_agent.knowledge.retriever import Retriever
from sa_resident_agent.knowledge.vector_store import VectorStore

logging.basicConfig(level=logging.WARNING)  # suppress info logs for clean REPL output


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="SA Resident Agent — Interactive Query")
    parser.add_argument(
        "--provider",
        choices=["CPS_ENERGY", "SAWS", "CITY_SA"],
        default=None,
        help="Filter results to a specific provider (default: all)",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Number of results to return per query (default: 5)",
    )
    parser.add_argument(
        "--chroma-path",
        default="data/chroma",
        help="Path to ChromaDB persist directory",
    )
    return parser.parse_args()


def print_results(results, query: str):
    if not results:
        print("\n⚠️  No results found. Is the index built? Run: python main.py\n")
        return

    print(f"\n{'='*60}")
    print(f"Query: {query}")
    print(f"Results: {len(results)}")
    print(f"{'='*60}")
    for i, r in enumerate(results, 1):
        print(f"\n[{i}] Provider : {r.provider}")
        print(f"    Score    : {r.score:.4f}  (lower = more similar)")
        print(f"    URL      : {r.url}")
        print(f"    Title    : {r.title}")
        print(f"    Excerpt  : {r.text[:300].strip()}...")
    print()


def main():
    args = parse_args()

    # Show index stats
    store = VectorStore(persist_path=args.chroma_path)
    counts = store.count_by_provider()
    print("\n📚 Knowledge Base Status")
    print("-" * 40)
    for provider, count in counts.items():
        status = "✅" if count > 0 else "⚠️ "
        print(f"  {status} {provider:<14} {count:>4} chunks")
    print(f"  {'TOTAL':<16} {sum(counts.values()):>4} chunks")
    print("-" * 40)

    if sum(counts.values()) == 0:
        print("\n❌ Index is empty. Run: python main.py\n")
        sys.exit(1)

    retriever = Retriever(persist_path=args.chroma_path)
    provider_label = args.provider or "ALL"

    print(f"\n🔍 Querying provider: {provider_label} | top_k: {args.top_k}")
    print("Type your question and press Enter. Type 'exit' to quit.\n")

    while True:
        try:
            query = input("Query > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break

        if not query:
            continue
        if query.lower() in ("exit", "quit", "q"):
            print("Goodbye.")
            break

        results = retriever.query(query, provider=args.provider, top_k=args.top_k)
        print_results(results, query)


if __name__ == "__main__":
    main()
