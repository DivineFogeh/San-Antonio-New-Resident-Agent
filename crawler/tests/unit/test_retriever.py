"""tests/unit/test_retriever.py"""

import pytest
from sa_resident_agent.knowledge.retriever import Retriever
from sa_resident_agent.knowledge.vector_store import RetrievedChunk


@pytest.fixture(scope="module")
def retriever(temp_chroma_dir, populated_store):
    """Retriever backed by the session-scoped populated store."""
    return Retriever(persist_path=temp_chroma_dir)


def test_query_returns_results(retriever):
    results = retriever.query("CPS Energy electricity rates")
    assert len(results) > 0


def test_query_returns_retrieved_chunks(retriever):
    results = retriever.query("water service SAWS")
    for r in results:
        assert isinstance(r, RetrievedChunk)


def test_cps_query_returns_results(retriever):
    results = retriever.query("electricity rates", provider="CPS_ENERGY")
    assert len(results) > 0
    for r in results:
        assert r.provider == "CPS_ENERGY"


def test_saws_query_returns_results(retriever):
    results = retriever.query("water deposit", provider="SAWS")
    assert len(results) > 0
    for r in results:
        assert r.provider == "SAWS"


def test_city_sa_query_returns_results(retriever):
    results = retriever.query("building permits 311", provider="CITY_SA")
    assert len(results) > 0
    for r in results:
        assert r.provider == "CITY_SA"


def test_empty_query_returns_empty(retriever):
    results = retriever.query("")
    assert results == []


def test_top_k_respected(retriever):
    results = retriever.query("service", top_k=2)
    assert len(results) <= 2


def test_results_have_score(retriever):
    results = retriever.query("new resident utilities")
    for r in results:
        assert isinstance(r.score, float)
