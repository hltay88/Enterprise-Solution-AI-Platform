"""Sprint 5.2 — local embedding + chunking + RRF unit tests."""

from app.ai.embeddings.local_provider import LocalHashEmbeddingProvider
from app.constants.knowledge_lifecycle import RETRIEVAL_ELIGIBLE_STATUSES
from app.services.knowledge_chunking import chunk_knowledge_text
from app.services.retrieval_service import RetrievalService


def test_local_embedder_is_deterministic_and_normalized():
    provider = LocalHashEmbeddingProvider(dimensions=32)
    a = provider.embed_query("high density wifi design")
    b = provider.embed_query("high density wifi design")
    c = provider.embed_query("unrelated billing invoice text")
    assert a == b
    assert len(a) == 32
    assert abs(sum(v * v for v in a) - 1.0) < 1e-6
    # Different text should generally differ
    assert a != c


def test_chunk_knowledge_text_windows():
    text = ("word " * 400).strip()
    chunks = chunk_knowledge_text(text, chunk_size=100, overlap=20)
    assert len(chunks) > 1
    assert chunks[0].chunk_index == 0
    assert all(c.text for c in chunks)


def test_retrieval_eligible_statuses():
    assert "published" in RETRIEVAL_ELIGIBLE_STATUSES
    assert "approved" in RETRIEVAL_ELIGIBLE_STATUSES
    assert "draft" not in RETRIEVAL_ELIGIBLE_STATUSES


def test_rrf_fuse_prefers_overlap():
    v = [
        {"chunk_id": "a", "content": "A", "knowledge_item_id": "i1", "vector_score": 0.9},
        {"chunk_id": "b", "content": "B", "knowledge_item_id": "i2", "vector_score": 0.8},
    ]
    k = [
        {"chunk_id": "a", "content": "A", "knowledge_item_id": "i1", "keyword_score": 0.7},
        {"chunk_id": "c", "content": "C", "knowledge_item_id": "i3", "keyword_score": 0.6},
    ]
    fused = RetrievalService._rrf_fuse(v, k, top_k=3)
    assert fused[0]["chunk_id"] == "a"
    assert fused[0]["fused_score"] > fused[1]["fused_score"]
