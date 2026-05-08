"""
sa_resident_agent/knowledge/vector_store.py

ChromaDB persistence layer. Stores chunks + embeddings and supports
filtered semantic search by provider.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

import chromadb
from chromadb.config import Settings

from sa_resident_agent.knowledge.chunker import DocumentChunk

logger = logging.getLogger(__name__)

COLLECTION_NAME = "sa_resident_knowledge"
CHROMA_PATH = "data/chroma"


@dataclass
class RetrievedChunk:
    chunk_id: str
    text: str
    url: str
    provider: str
    title: str
    score: float  # cosine distance (lower = more similar)


class VectorStore:
    def __init__(self, persist_path: str = CHROMA_PATH):
        self.client = chromadb.PersistentClient(
            path=persist_path,
            settings=Settings(anonymized_telemetry=False),
        )
        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(f"ChromaDB collection '{COLLECTION_NAME}' ready. Docs: {self.collection.count()}")

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def add_chunks(self, chunks: list[DocumentChunk], embeddings: list[list[float]]) -> None:
        """Upsert chunks + precomputed embeddings into ChromaDB."""
        if not chunks:
            logger.warning("add_chunks called with empty list — nothing to add.")
            return

        ids = [c.chunk_id for c in chunks]
        documents = [c.text for c in chunks]
        metadatas = [
            {
                "url": c.url,
                "provider": c.provider,
                "title": c.title,
                "scraped_at": c.scraped_at,
                "chunk_index": c.chunk_index,
            }
            for c in chunks
        ]

        # Chroma upsert in batches of 500 to avoid payload limits
        batch_size = 500
        for i in range(0, len(ids), batch_size):
            self.collection.upsert(
                ids=ids[i : i + batch_size],
                embeddings=embeddings[i : i + batch_size],
                documents=documents[i : i + batch_size],
                metadatas=metadatas[i : i + batch_size],
            )
            logger.debug(f"Upserted batch {i // batch_size + 1} ({len(ids[i:i+batch_size])} docs)")

        logger.info(f"Added {len(chunks)} chunks. Collection total: {self.collection.count()}")

    def delete_provider(self, provider: str) -> None:
        """Delete all chunks for a given provider (used for re-indexing)."""
        results = self.collection.get(where={"provider": provider})
        ids_to_delete = results["ids"]
        if ids_to_delete:
            self.collection.delete(ids=ids_to_delete)
            logger.info(f"Deleted {len(ids_to_delete)} chunks for provider '{provider}'")
        else:
            logger.info(f"No chunks found for provider '{provider}' — nothing deleted.")

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def query(
        self,
        query_embedding: list[float],
        provider: Optional[str] = None,
        top_k: int = 5,
    ) -> list[RetrievedChunk]:
        """
        Semantic search. Optional provider filter (e.g. 'CPS_ENERGY').
        Returns top_k results sorted by relevance.
        """
        where = {"provider": provider} if provider else None

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where,
            include=["documents", "metadatas", "distances"],
        )

        chunks = []
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            chunks.append(RetrievedChunk(
                chunk_id=results["ids"][0][len(chunks)],
                text=doc,
                url=meta["url"],
                provider=meta["provider"],
                title=meta.get("title", ""),
                score=dist,
            ))

        return chunks

    def count(self) -> int:
        return self.collection.count()

    def count_by_provider(self) -> dict[str, int]:
        """Return doc count per provider."""
        providers = ["CPS_ENERGY", "SAWS", "CITY_SA"]
        counts = {}
        for p in providers:
            results = self.collection.get(where={"provider": p})
            counts[p] = len(results["ids"])
        return counts
