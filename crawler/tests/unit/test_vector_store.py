"""tests/unit/test_vector_store.py"""

from sa_resident_agent.knowledge.vector_store import RetrievedChunk


def test_store_count_increases_after_add(populated_store):
    assert populated_store.count() > 0


def test_query_returns_list(populated_store, embedder):
    embedding = embedder.embed_query("electricity rates")
    results = populated_store.query(embedding, top_k=3)
    assert isinstance(results, list)


def test_query_returns_retrieved_chunks(populated_store, embedder):
    embedding = embedder.embed_query("CPS Energy residential rate")
    results = populated_store.query(embedding, top_k=3)
    for r in results:
        assert isinstance(r, RetrievedChunk)


def test_query_respects_top_k(populated_store, embedder):
    embedding = embedder.embed_query("water service deposit")
    results = populated_store.query(embedding, top_k=2)
    assert len(results) <= 2


def test_query_provider_filter_cps(populated_store, embedder):
    embedding = embedder.embed_query("electricity")
    results = populated_store.query(embedding, provider="CPS_ENERGY", top_k=5)
    for r in results:
        assert r.provider == "CPS_ENERGY"


def test_query_provider_filter_saws(populated_store, embedder):
    embedding = embedder.embed_query("water")
    results = populated_store.query(embedding, provider="SAWS", top_k=5)
    for r in results:
        assert r.provider == "SAWS"


def test_query_provider_filter_city(populated_store, embedder):
    embedding = embedder.embed_query("permits")
    results = populated_store.query(embedding, provider="CITY_SA", top_k=5)
    for r in results:
        assert r.provider == "CITY_SA"


def test_retrieved_chunk_has_required_fields(populated_store, embedder):
    embedding = embedder.embed_query("start service")
    results = populated_store.query(embedding, top_k=1)
    assert len(results) > 0
    r = results[0]
    assert r.chunk_id
    assert r.text
    assert r.url
    assert r.provider
    assert isinstance(r.score, float)


def test_count_by_provider_returns_all_providers(populated_store):
    counts = populated_store.count_by_provider()
    assert "CPS_ENERGY" in counts
    assert "SAWS"       in counts
    assert "CITY_SA"    in counts
    assert all(v >= 0 for v in counts.values())
