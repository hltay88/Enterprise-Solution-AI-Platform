"""Gemini embeddings adapter (optional). Pads/truncates to configured dims."""

from __future__ import annotations

import logging
import math

from app.ai.embeddings.base import EmbeddingProvider
from app.core.config import settings
from app.core.exceptions import ValidationAppError

logger = logging.getLogger(__name__)


def _fit_dims(vec: list[float], dims: int) -> list[float]:
    if len(vec) == dims:
        return vec
    if len(vec) > dims:
        clipped = vec[:dims]
    else:
        clipped = vec + [0.0] * (dims - len(vec))
    norm = math.sqrt(sum(v * v for v in clipped)) or 1.0
    return [v / norm for v in clipped]


class GeminiEmbeddingProvider(EmbeddingProvider):
    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str | None = None,
        dimensions: int | None = None,
    ) -> None:
        self._api_key = api_key or settings.effective_gemini_api_key
        if not self._api_key:
            raise ValidationAppError("GEMINI_API_KEY is required for Gemini embeddings")
        self._model = (model or settings.atlas_embedding_model or "gemini-embedding-001").strip()
        self._dimensions = int(dimensions or settings.atlas_embedding_dims or 384)

    @property
    def name(self) -> str:
        return "gemini"

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
            from google import genai
        except ImportError as exc:
            raise ValidationAppError("google-genai package is required for Gemini embeddings") from exc

        client = genai.Client(api_key=self._api_key)
        vectors: list[list[float]] = []
        for text in texts:
            payload = text if text.strip() else " "
            try:
                result = client.models.embed_content(model=self._model, contents=payload)
                values = list(getattr(result, "embeddings", [None])[0].values)  # type: ignore[union-attr]
            except Exception:
                # Older / alternate response shapes
                result = client.models.embed_content(model=self._model, contents=payload)
                embedding = getattr(result, "embedding", None)
                if embedding is not None and hasattr(embedding, "values"):
                    values = list(embedding.values)
                elif isinstance(result, dict) and "embedding" in result:
                    values = list(result["embedding"])
                else:
                    raise
            vectors.append(_fit_dims([float(v) for v in values], self._dimensions))
        return vectors
