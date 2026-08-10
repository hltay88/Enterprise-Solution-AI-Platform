"""Embedding provider factory (Sprint 5.2)."""

from __future__ import annotations

import logging

from app.ai.embeddings.base import EmbeddingProvider
from app.ai.embeddings.fallback_provider import FallbackEmbeddingProvider
from app.ai.embeddings.local_provider import LocalHashEmbeddingProvider
from app.core.config import settings

logger = logging.getLogger(__name__)


def get_embedding_provider() -> EmbeddingProvider:
    """Return configured embedding provider.

    Modes:
    - local: deterministic hash embedder
    - gemini / openai: cloud only
    - auto: gemini (keyed) -> openai (keyed) -> local, with runtime fallback
    """
    mode = (settings.atlas_embedding_provider or "auto").strip().lower()
    dims = int(settings.atlas_embedding_dims or 384)
    local = LocalHashEmbeddingProvider(dimensions=dims)

    if mode == "local":
        return local

    if mode == "gemini":
        from app.ai.embeddings.gemini_provider import GeminiEmbeddingProvider

        return GeminiEmbeddingProvider(dimensions=dims)

    if mode == "openai":
        from app.ai.embeddings.openai_provider import OpenAIEmbeddingProvider

        return OpenAIEmbeddingProvider(dimensions=dims)

    chain: list[EmbeddingProvider] = []
    if settings.effective_gemini_api_key:
        try:
            from app.ai.embeddings.gemini_provider import GeminiEmbeddingProvider

            chain.append(GeminiEmbeddingProvider(dimensions=dims))
        except Exception as exc:
            logger.warning("Gemini embedding init failed (%s)", exc)
    if settings.openai_api_key:
        try:
            from app.ai.embeddings.openai_provider import OpenAIEmbeddingProvider

            chain.append(OpenAIEmbeddingProvider(dimensions=dims))
        except Exception as exc:
            logger.warning("OpenAI embedding init failed (%s)", exc)
    chain.append(local)
    if len(chain) == 1:
        return chain[0]
    return FallbackEmbeddingProvider(providers=chain)
