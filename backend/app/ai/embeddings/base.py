"""Sprint 5.2 — provider-neutral embedding interface."""

from __future__ import annotations

from abc import ABC, abstractmethod


class EmbeddingProvider(ABC):
    """Vendor-neutral embeddings for knowledge indexing and retrieval."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider id recorded on chunks / retrieval runs."""

    @property
    @abstractmethod
    def model(self) -> str:
        """Model id recorded on chunks / retrieval runs."""

    @property
    @abstractmethod
    def dimensions(self) -> int:
        """Vector dimensionality (must match knowledge_chunks.embedding)."""

    @abstractmethod
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed corpus chunks (may batch internally)."""

    def embed_query(self, text: str) -> list[float]:
        """Embed a single query string."""
        vectors = self.embed_documents([text])
        return vectors[0] if vectors else [0.0] * self.dimensions
