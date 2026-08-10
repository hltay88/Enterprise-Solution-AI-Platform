"""Sprint 5.1 — Enterprise Knowledge lifecycle states and transitions."""

from __future__ import annotations

STATUS_DRAFT = "draft"
STATUS_REVIEW = "review"
STATUS_APPROVED = "approved"
STATUS_PUBLISHED = "published"
STATUS_DEPRECATED = "deprecated"
STATUS_ARCHIVED = "archived"

KNOWLEDGE_STATUSES: frozenset[str] = frozenset(
    {
        STATUS_DRAFT,
        STATUS_REVIEW,
        STATUS_APPROVED,
        STATUS_PUBLISHED,
        STATUS_DEPRECATED,
        STATUS_ARCHIVED,
    }
)

# Legal single-step transitions (from → allowed destinations).
ALLOWED_TRANSITIONS: dict[str, frozenset[str]] = {
    STATUS_DRAFT: frozenset({STATUS_REVIEW}),
    STATUS_REVIEW: frozenset({STATUS_APPROVED, STATUS_DRAFT}),
    STATUS_APPROVED: frozenset({STATUS_PUBLISHED, STATUS_REVIEW}),
    STATUS_PUBLISHED: frozenset({STATUS_DEPRECATED}),
    STATUS_DEPRECATED: frozenset({STATUS_ARCHIVED}),
    STATUS_ARCHIVED: frozenset(),
}

# Statuses that are immutable content snapshots (no in-place edit).
IMMUTABLE_STATUSES: frozenset[str] = frozenset(
    {
        STATUS_PUBLISHED,
        STATUS_DEPRECATED,
        STATUS_ARCHIVED,
    }
)

# Eligible for future production retrieval (Sprint 5.2) — not used for search yet.
RETRIEVAL_ELIGIBLE_STATUSES: frozenset[str] = frozenset(
    {
        STATUS_APPROVED,
        STATUS_PUBLISHED,
    }
)


def normalize_status(status: str | None) -> str:
    cleaned = (status or STATUS_DRAFT).strip().lower()
    if cleaned not in KNOWLEDGE_STATUSES:
        raise ValueError(f"Unknown knowledge status: {status}")
    return cleaned


def can_transition(current: str, target: str) -> bool:
    return normalize_status(target) in ALLOWED_TRANSITIONS.get(
        normalize_status(current),
        frozenset(),
    )
