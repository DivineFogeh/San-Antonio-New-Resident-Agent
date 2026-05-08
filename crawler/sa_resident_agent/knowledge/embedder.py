"""
sa_resident_agent/knowledge/embedder.py

Encodes DocumentChunks into dense vectors using sentence-transformers.
Model: all-MiniLM-L6-v2 (384-dim, runs on CPU, no API key needed).
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from sentence_transformers import SentenceTransformer

if TYPE_CHECKING:
    from sa_resident_agent.knowledge.chunker import DocumentChunk

logger = logging.getLogger(__name__)

MODEL_NAME = "all-MiniLM-L6-v2"
BATCH_SIZE = 64


class Embedder:
    def __init__(self, model_name: str = MODEL_NAME):
        logger.info(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.model_name = model_name
        logger.info("Embedding model loaded.")

    def embed_chunks(self, chunks: list["DocumentChunk"]) -> list[list[float]]:
        """Return a list of embedding vectors (one per chunk)."""
        texts = [chunk.text for chunk in chunks]
        logger.info(f"Embedding {len(texts)} chunks in batches of {BATCH_SIZE}...")

        embeddings = self.model.encode(
            texts,
            batch_size=BATCH_SIZE,
            show_progress_bar=True,
            convert_to_numpy=True,
        )

        logger.info("Embedding complete.")
        return embeddings.tolist()

    def embed_query(self, query: str) -> list[float]:
        """Embed a single query string for retrieval."""
        return self.model.encode(query, convert_to_numpy=True).tolist()
