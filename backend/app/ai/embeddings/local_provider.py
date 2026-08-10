"""Deterministic local embedding for Mac offline + tests (no cloud keys)."""

from __future__ import annotations

import hashlib
import math
import re

from app.ai.embeddings.base import EmbeddingProvider
from app.core.config import settings

_TOKEN_RE = re.compile(r"[a-z0-9_]+", re.IGNORECASE)


def _tokenize(text: str) -> list[str]:
    return [t.lower() for t in _TOKEN_RE.findall(text or "") if t]


def _l2_normalize(vec: list[float]) -> list[float]:
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


class LocalHashEmbeddingProvider(EmbeddingProvider):
    """Feature-hash bag-of-tokens projected into a fixed dimension."""

    def __init__(self, dimensions: int | None = None) -> None:
        self._dimensions = int(dimensions or settings.atlas_embedding_dims or 384)

    @property
    def name(self) -> str:
        return "local"

    @property
    def model(self) -> str:
        return f"local-hash-v1-d{self._dimensions}"

    @property
    def dimensions(self) -> int:
        return self._dimensions

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_one(text) for text in texts]

    def _embed_one(self, text: str) -> list[float]:
        vec = [0.0] * self._dimensions
        tokens = _tokenize(text)
        if not tokens:
            return _l2_normalize(vec)
        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            # Use first 8 bytes for index, next for sign.
            idx = int.from_bytes(digest[:4], "little") % self._dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            weight = 1.0 + (digest[5] / 255.0)
            vec[idx] += sign * weight
        return _l2_normalize(vec)
