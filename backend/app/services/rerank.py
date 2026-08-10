"""Local portable re-ranker (Phase 5 complete — no cloud ML dependency).

Applies lexical overlap + RRF score blending, optional freshness, then diversity.
"""

from __future__ import annotations

import math
import re
from datetime import datetime, timezone
from typing import Any


_TOKEN = re.compile(r"[a-z0-9]{2,}", re.I)


def _tokens(text: str) -> set[str]:
    return {t.lower() for t in _TOKEN.findall(text or "")}


def lexical_overlap_score(query: str, content: str) -> float:
    q = _tokens(query)
    if not q:
        return 0.0
    c = _tokens(content)
    if not c:
        return 0.0
    return len(q & c) / len(q)


def freshness_boost(published_at: datetime | None, *, now: datetime | None = None) -> float:
    """Gentle boost for newer content (0..0.15)."""
    if published_at is None:
        return 0.0
    now = now or datetime.now(timezone.utc)
    if published_at.tzinfo is None:
        published_at = published_at.replace(tzinfo=timezone.utc)
    age_days = max(0.0, (now - published_at).total_seconds() / 86400.0)
    # Half-life ~365 days
    return 0.15 * math.exp(-age_days / 365.0)


def rerank_hits(
    query: str,
    hits: list[dict[str, Any]],
    *,
    top_k: int,
    rrf_weight: float = 0.55,
    lexical_weight: float = 0.35,
    freshness_weight: float = 0.10,
) -> list[dict[str, Any]]:
    """Re-rank fused hits. Mutates copies; returns new ordered list."""
    scored: list[dict[str, Any]] = []
    max_rrf = max((float(h.get("fused_score") or 0.0) for h in hits), default=0.0) or 1.0
    for hit in hits:
        row = dict(hit)
        rrf_norm = float(row.get("fused_score") or 0.0) / max_rrf
        lex = lexical_overlap_score(query, str(row.get("content") or ""))
        fresh = freshness_boost(row.get("published_at"))
        final = (rrf_weight * rrf_norm) + (lexical_weight * lex) + (freshness_weight * fresh)
        row["rerank_score"] = final
        row["lexical_score"] = lex
        row["freshness_score"] = fresh
        # Keep fused_score as final display score for API compatibility
        row["fused_score"] = final
        scored.append(row)
    scored.sort(key=lambda h: float(h.get("rerank_score") or 0.0), reverse=True)
    return scored[: max(1, top_k)]
