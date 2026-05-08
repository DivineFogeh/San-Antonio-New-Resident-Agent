"""tests/unit/test_embedder.py"""



def test_embed_query_returns_list(embedder):
    result = embedder.embed_query("What are the CPS Energy rates?")
    assert isinstance(result, list)


def test_embed_query_correct_dimension(embedder):
    result = embedder.embed_query("How do I start SAWS water service?")
    assert len(result) == 384


def test_embed_query_returns_floats(embedder):
    result = embedder.embed_query("City of San Antonio permits")
    assert all(isinstance(v, float) for v in result)


def test_embed_chunks_returns_correct_count(embedder, chunker, sample_cps_page):
    chunks = chunker.chunk(sample_cps_page)
    embeddings = embedder.embed_chunks(chunks)
    assert len(embeddings) == len(chunks)


def test_embed_chunks_correct_dimension(embedder, chunker, sample_cps_page):
    chunks = chunker.chunk(sample_cps_page)
    embeddings = embedder.embed_chunks(chunks)
    for emb in embeddings:
        assert len(emb) == 384


def test_different_queries_produce_different_embeddings(embedder):
    e1 = embedder.embed_query("electricity rates CPS Energy")
    e2 = embedder.embed_query("water service SAWS deposit")
    assert e1 != e2


def test_same_query_produces_same_embedding(embedder):
    q = "What documents do I need for SAWS?"
    e1 = embedder.embed_query(q)
    e2 = embedder.embed_query(q)
    assert e1 == e2
