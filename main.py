"""
main.py

Entry point — runs the full crawl → chunk → embed → store pipeline.

Usage:
    python main.py                        # build all three providers
    python main.py --providers CPS_ENERGY SAWS   # specific providers
    python main.py --rebuild              # delete and re-index everything
    python main.py --providers CPS_ENERGY --rebuild  # rebuild one provider
"""

import argparse
import logging
import sys

from sa_resident_agent.knowledge.index_builder import IndexBuilder

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

VALID_PROVIDERS = ["CPS_ENERGY", "SAWS", "CITY_SA"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="SA Resident Agent — Index Builder")
    parser.add_argument(
        "--providers",
        nargs="+",
        choices=VALID_PROVIDERS,
        default=VALID_PROVIDERS,
        help="Which providers to crawl and index (default: all)",
    )
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Delete existing index entries before re-indexing",
    )
    parser.add_argument(
        "--chroma-path",
        default="data/chroma",
        help="Path to ChromaDB persist directory (default: data/chroma)",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    logger.info("=" * 60)
    logger.info("SA Resident Agent — Index Builder")
    logger.info(f"Providers : {args.providers}")
    logger.info(f"Rebuild   : {args.rebuild}")
    logger.info(f"ChromaDB  : {args.chroma_path}")
    logger.info("=" * 60)

    builder = IndexBuilder(persist_path=args.chroma_path)
    results = builder.build(providers=args.providers, rebuild=args.rebuild)

    logger.info("\n" + "=" * 60)
    logger.info("BUILD SUMMARY")
    logger.info("=" * 60)
    all_ok = True
    for r in results:
        status = "✅ OK" if r.success else "❌ FAILED"
        logger.info(
            f"{status}  {r.provider:<12} "
            f"pages={r.pages_crawled:>3}  chunks={r.chunks_indexed:>4}"
        )
        if r.errors:
            for err in r.errors:
                logger.warning(f"         ↳ {err}")
        if not r.success:
            all_ok = False

    logger.info("=" * 60)
    if all_ok:
        logger.info("All providers indexed successfully. Run query.py to test retrieval.")
    else:
        logger.warning("Some providers failed — check logs above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
