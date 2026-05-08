"""
sa_resident_agent/knowledge/chunker.py

Splits raw CrawledPage text into overlapping chunks with metadata.
Uses LangChain's RecursiveCharacterTextSplitter.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from langchain_text_splitters import RecursiveCharacterTextSplitter

from sa_resident_agent.crawlers.base_crawler import CrawledPage

logger = logging.getLogger(__name__)

CHUNK_SIZE = 512        # characters (approx ~128 tokens for MiniLM)
CHUNK_OVERLAP = 64      # characters overlap between chunks


@dataclass
class DocumentChunk:
    chunk_id: str       # "{url_hash}_{chunk_index}"
    text: str
    url: str
    provider: str
    title: str
    scraped_at: str
    chunk_index: int


class Chunker:
    def __init__(self, chunk_size: int = CHUNK_SIZE, chunk_overlap: int = CHUNK_OVERLAP):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

    def chunk(self, page: CrawledPage) -> list[DocumentChunk]:
        """Split a single CrawledPage into DocumentChunks."""
        if not page.text or len(page.text.strip()) < 50:
            logger.warning(f"Skipping near-empty page: {page.url}")
            return []

        raw_chunks = self.splitter.split_text(page.text)
        url_hash = abs(hash(page.url)) % (10 ** 8)

        chunks = []
        for i, text in enumerate(raw_chunks):
            if len(text.strip()) < 30:
                continue  # skip trivially short chunks
            chunks.append(DocumentChunk(
                chunk_id=f"{url_hash}_{i:04d}",
                text=text.strip(),
                url=page.url,
                provider=page.provider,
                title=page.title,
                scraped_at=page.scraped_at,
                chunk_index=i,
            ))

        logger.debug(f"Chunked {page.url} → {len(chunks)} chunks")
        return chunks

    def chunk_all(self, pages: list[CrawledPage]) -> list[DocumentChunk]:
        """Chunk a list of CrawledPages. Returns all chunks."""
        all_chunks = []
        for page in pages:
            all_chunks.extend(self.chunk(page))
        logger.info(f"Total chunks produced: {len(all_chunks)} from {len(pages)} pages")
        return all_chunks
