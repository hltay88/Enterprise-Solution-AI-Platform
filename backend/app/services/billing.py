"""Billing abstraction — metered local provider for Phase 5 completion."""

from __future__ import annotations

from typing import Any, Protocol
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import settings


class BillingProvider(Protocol):
    def report_usage(
        self,
        *,
        tenant_id: UUID | None,
        event_type: str,
        quantity: float = 1.0,
        metadata: dict[str, Any] | None = None,
    ) -> None: ...

    def estimate_cost_usd(self, *, event_type: str, quantity: float = 1.0) -> float: ...


# Rough portable unit prices for observability (not real vendor billing)
_UNIT_COST = {
    "retrieval": 0.0002,
    "embedding": 0.00005,
    "agent_run": 0.002,
    "ai_completion": 0.001,
    "generation": 0.003,
}


class NoopBillingProvider:
    def report_usage(
        self,
        *,
        tenant_id: UUID | None,
        event_type: str,
        quantity: float = 1.0,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        _ = (tenant_id, event_type, quantity, metadata)

    def estimate_cost_usd(self, *, event_type: str, quantity: float = 1.0) -> float:
        return 0.0


class MeteredBillingProvider:
    """Local metered provider — estimates cost and can stamp usage metadata."""

    def __init__(self, db: Session | None = None) -> None:
        self.db = db

    def estimate_cost_usd(self, *, event_type: str, quantity: float = 1.0) -> float:
        unit = _UNIT_COST.get(event_type, 0.0001)
        return round(unit * max(quantity, 0.0), 6)

    def report_usage(
        self,
        *,
        tenant_id: UUID | None,
        event_type: str,
        quantity: float = 1.0,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        # Metering is observational; UsageService.record is the persistence path.
        # This method exists so callers can obtain cost estimates consistently.
        _ = (tenant_id, event_type, quantity, metadata)
        return None


def get_billing_provider(db: Session | None = None) -> BillingProvider:
    mode = (getattr(settings, "atlas_billing_provider", "metered") or "metered").lower()
    if mode == "noop":
        return NoopBillingProvider()
    return MeteredBillingProvider(db=db)
