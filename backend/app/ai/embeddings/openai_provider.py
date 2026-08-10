"""OpenAI embeddings adapter (optional; dimensions matched via API param)."""

from __future__ import annotations

import logging

from app.ai.embeddings.base import EmbeddingProvider
from app.core.config import settings
from app.core.exceptions import ValidationAppError

logger = logging.getLogger(__name__)


class OpenAIEmbeddingProvider(EmbeddingProvider):
    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str | None = None,
        dimensions: int | None = None,
    ) -> None:
        self._api_key = api_key or settings.openai_api_key
        if not self._api_key:
            raise ValidationAppError("OPENAI_API_KEY is required for OpenAI embeddings")
        self._model = (model or settings.atlas_embedding_model or "text-embedding-3-small").strip()
        self._dimensions = int(dimensions or settings.atlas_embedding_dims or 384)

    @property
    def name(self) -> str:
        return "openai"

    @property
    def model(self) -> str:
        return self._model

    @property
    def dimensions(self) -> int:
        return self._dimensions

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise ValidationAppError("openai package is required for OpenAI embeddings") from exc

        client = OpenAI(api_key=self._api_key)
        # Batch modestly for Mac/dev.
        out: list[list[float]] = []
        batch_size = 64
        for start in range(0, len(texts), batch_size):
            batch = [t if t.strip() else " " for t in texts[start : start + batch_size]]
            response = client.embeddings.create(
                model=self._model,
                input=batch,
                dimensions=self._dimensions,
            )
            # API returns data possibly unordered — sort by index.
            ordered = sorted(response.data, key=lambda row: row.index)
            out.extend([list(row.embedding) for row in ordered])
        return out
