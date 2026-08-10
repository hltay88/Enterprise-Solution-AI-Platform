"""Fallback chain for embeddings (mirror chat FallbackAIProvider)."""

from __future__ import annotations

import logging

from app.ai.embeddings.base import EmbeddingProvider

logger = logging.getLogger(__name__)


class FallbackEmbeddingProvider(EmbeddingProvider):
    def __init__(self, providers: list[EmbeddingProvider]) -> None:
        if not providers:
            raise ValueError("FallbackEmbeddingProvider requires at least one provider")
        self._providers = providers
        self._active = providers[0]

    @property
    def name(self) -> str:
        return self._active.name

    @property
    def model(self) -> str:
        return self._active.model

    @property
    def dimensions(self) -> int:
        return self._active.dimensions

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        last_error: Exception | None = None
        for provider in self._providers:
            try:
                vectors = provider.embed_documents(texts)
                self._active = provider
                return vectors
            except Exception as exc:
                last_error = exc
                logger.warning(
                    "Embedding provider %s failed (%s); trying next",
                    provider.name,
                    exc,
                )
        assert last_error is not None
        raise last_error
