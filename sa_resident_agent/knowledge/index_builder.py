"""
sa_resident_agent/knowledge/index_builder.py

Orchestrates the full pipeline:
    crawl → chunk → embed → store in ChromaDB

Called by main.py and by `make reproduce`.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from sa_resident_agent.crawlers.cps_crawler import CPSCrawler
from sa_resident_agent.crawlers.saws_crawler import SAWSCrawler
from sa_resident_agent.crawlers.city_crawler import CitySACrawler
from sa_resident_agent.knowledge.chunker import Chunker
from sa_resident_agent.knowledge.embedder import Embedder
from sa_resident_agent.knowledge.vector_store import VectorStore

logger = logging.getLogger(__name__)

CRAWLER_MAP = {
    "CPS_ENERGY": CPSCrawler,
    "SAWS": SAWSCrawler,
    "CITY_SA": CitySACrawler,
}


@dataclass
class IndexBuildResult:
    provider: str
    pages_crawled: int
    chunks_indexed: int
    errors: list[str] = field(default_factory=list)
    success: bool = True


class IndexBuilder:
    def __init__(self, persist_path: str = "data/chroma"):
        self.chunker = Chunker()
        self.embedder = Embedder()
        self.store = VectorStore(persist_path=persist_path)

    def build(
        self,
        providers: list[str] = None,
        rebuild: bool = False,
    ) -> list[IndexBuildResult]:
        """
        Crawl, chunk, embed, and store all specified providers.

        Args:
            providers: List of provider keys. Defaults to all three.
            rebuild:   If True, deletes existing chunks before re-indexing.

        Returns:
            List of IndexBuildResult — one per provider.
        """
        if providers is None:
            providers = list(CRAWLER_MAP.keys())

        results = []
        for provider in providers:
            result = self._build_provider(provider, rebuild=rebuild)
            results.append(result)

        # Summary
        total_pages = sum(r.pages_crawled for r in results)
        total_chunks = sum(r.chunks_indexed for r in results)
        logger.info(
            f"Index build complete. "
            f"Providers: {len(results)}, Pages: {total_pages}, Chunks: {total_chunks}"
        )
        return results

    def rebuild(self, provider: str) -> IndexBuildResult:
        """Drop and rebuild the index for a single provider."""
        return self._build_provider(provider, rebuild=True)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _build_provider(self, provider: str, rebuild: bool) -> IndexBuildResult:
        if provider not in CRAWLER_MAP:
            msg = f"Unknown provider: {provider}"
            logger.error(msg)
            return IndexBuildResult(provider=provider, pages_crawled=0, chunks_indexed=0,
                                    errors=[msg], success=False)

        logger.info(f"=== Building index for {provider} (rebuild={rebuild}) ===")

        if rebuild:
            self.store.delete_provider(provider)

        # 1. Crawl
        crawler_cls = CRAWLER_MAP[provider]
        crawler = crawler_cls()
        try:
            pages = crawler.crawl()
        except Exception as e:
            msg = f"Crawl failed for {provider}: {e}"
            logger.exception(msg)
            return IndexBuildResult(provider=provider, pages_crawled=0, chunks_indexed=0,
                                    errors=[msg], success=False)

        if not pages:
            msg = f"No pages crawled for {provider}"
            logger.warning(msg)
            return IndexBuildResult(provider=provider, pages_crawled=0, chunks_indexed=0,
                                    errors=[msg], success=False)

        # 2. Chunk
        chunks = self.chunker.chunk_all(pages)
        if not chunks:
            msg = f"No chunks produced for {provider}"
            logger.warning(msg)
            return IndexBuildResult(provider=provider, pages_crawled=len(pages),
                                    chunks_indexed=0, errors=[msg], success=False)

        # 3. Embed
        embeddings = self.embedder.embed_chunks(chunks)

        # 4. Store
        self.store.add_chunks(chunks, embeddings)

        logger.info(
            f"[{provider}] Done — pages: {len(pages)}, chunks: {len(chunks)}"
        )
        return IndexBuildResult(
            provider=provider,
            pages_crawled=len(pages),
            chunks_indexed=len(chunks),
            success=True,
        )
