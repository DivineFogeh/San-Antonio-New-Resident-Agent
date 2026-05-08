"""
sa_resident_agent/knowledge/retriever.py

Public retriever interface used by the agent layer.
Wraps Embedder + VectorStore into a single query call.
"""

from __future__ import annotations

import logging
from typing import Optional

from sa_resident_agent.knowledge.embedder import Embedder
from sa_resident_agent.knowledge.vector_store import VectorStore, RetrievedChunk

logger = logging.getLogger(__name__)


class Retriever:
    def __init__(self, persist_path: str = "data/chroma"):
        self.embedder = Embedder()
        self.store = VectorStore(persist_path=persist_path)

    def query(
        self,
        text: str,
        provider: Optional[str] = None,
        top_k: int = 5,
    ) -> list[RetrievedChunk]:
        """
        Embed the query text and return top_k semantically similar chunks.

        Args:
            text:     Natural language query.
            provider: Optional filter — 'CPS_ENERGY', 'SAWS', or 'CITY_SA'.
            top_k:    Number of results to return.

        Returns:
            List of RetrievedChunk sorted by relevance (ascending distance).
        """
        if not text.strip():
            return []

        embedding = self.embedder.embed_query(text)
        results = self.store.query(embedding, provider=provider, top_k=top_k)
        logger.debug(f"Query '{text[:60]}...' returned {len(results)} chunks")
        return results
