"""tests/unit/test_chunker.py"""

from sa_resident_agent.crawlers.base_crawler import CrawledPage
from sa_resident_agent.knowledge.chunker import DocumentChunk


def test_chunk_returns_list(chunker, sample_cps_page):
    chunks = chunker.chunk(sample_cps_page)
    assert isinstance(chunks, list)
    assert len(chunks) > 0


def test_chunk_produces_document_chunks(chunker, sample_cps_page):
    for c in chunker.chunk(sample_cps_page):
        assert isinstance(c, DocumentChunk)


def test_chunk_metadata_populated(chunker, sample_cps_page):
    for c in chunker.chunk(sample_cps_page):
        assert c.url      == sample_cps_page.url
        assert c.provider == "CPS_ENERGY"
        assert c.title    == sample_cps_page.title
        assert c.chunk_id is not None


def test_chunk_ids_are_unique(chunker, sample_cps_page):
    chunks = chunker.chunk(sample_cps_page)
    ids = [c.chunk_id for c in chunks]
    assert len(ids) == len(set(ids))


def test_chunk_text_not_empty(chunker, sample_cps_page):
    for c in chunker.chunk(sample_cps_page):
        assert len(c.text.strip()) >= 30


def test_empty_page_returns_no_chunks(chunker):
    page = CrawledPage(url="https://example.com", provider="CPS_ENERGY",
                       title="Empty", text="   ", scraped_at="2026-05-01T00:00:00+00:00")
    assert chunker.chunk(page) == []


def test_short_page_returns_no_chunks(chunker):
    page = CrawledPage(url="https://example.com", provider="SAWS",
                       title="Short", text="Too short.", scraped_at="2026-05-01T00:00:00+00:00")
    assert chunker.chunk(page) == []


def test_chunk_all_covers_all_providers(chunker, all_sample_pages):
    chunks = chunker.chunk_all(all_sample_pages)
    providers = {c.provider for c in chunks}
    assert providers == {"CPS_ENERGY", "SAWS", "CITY_SA"}


def test_chunk_index_is_sequential(chunker, sample_saws_page):
    chunks = chunker.chunk(sample_saws_page)
    for i, c in enumerate(chunks):
        assert c.chunk_index == i
