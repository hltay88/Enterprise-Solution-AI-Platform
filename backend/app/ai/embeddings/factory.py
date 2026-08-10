"""Embedding provider factory (Sprint 5.2)."""

from __future__ import annotations

import logging

from app.ai.embeddings.base import EmbeddingProvider
from app.ai.embeddings.local_provider import LocalHashEmbeddingProvider
from app.core.config import settings

logger = logging.getLogger(__name__)


def get_embedding_provider() -> EmbeddingProvider:
    """Return configured embedding provider.

    Modes:
    - local: deterministic hash embedder
    - gemini / openai: cloud only
    - auto: gemini (keyed) -> openai (keyed) -> local
    """
    mode = (settings.atlas_embedding_provider or "auto").strip().lower()
    dims = int(settings.atlas_embedding_dims or 384)

    if mode == "local":
        return LocalHashEmbeddingProvider(dimensions=dims)

    if mode == "gemini":
        from app.ai.embeddings.gemini_provider import GeminiEmbeddingProvider

        return GeminiEmbeddingProvider(dimensions=dims)

    if mode == "openai":
        from app.ai.embeddings.openai_provider import OpenAIEmbeddingProvider

        return OpenAIEmbeddingProvider(dimensions=dims)

    # auto
    if settings.effective_gemini_api_key:
        try:
            from app.ai.embeddings.gemini_provider import GeminiEmbeddingProvider

            return GeminiEmbeddingProvider(dimensions=dims)
        except Exception as exc:
            logger.warning("Gemini embedding unavailable (%s); trying OpenAI/local", exc)
    if settings.openai_api_key:
        try:
            from app.ai.embeddings.openai_provider import OpenAIEmbeddingProvider

            return OpenAIEmbeddingProvider(dimensions=dims)
        except Exception as exc:
            logger.warning("OpenAI embedding unavailable (%s); using local", exc)
    return LocalHashEmbeddingProvider(dimensions=dims)
