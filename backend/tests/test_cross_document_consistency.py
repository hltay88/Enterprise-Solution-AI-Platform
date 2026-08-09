"""Cross-document consistency unit helpers."""

from app.services.cross_document_consistency_service import _normalize


def test_normalize_strips_stopwords():
    tokens = _normalize("The Approved Architecture and Solution Design for Customer")
    assert "architecture" not in tokens
    assert "solution" not in tokens
    assert "customer" not in tokens
