"""Billing abstraction (Sprint 5.5) — local noop provider."""

from __future__ import annotations

from typing import Any, Protocol
from uuid import UUID


class BillingProvider(Protocol):
    def report_usage(
        self,
        *,
        tenant_id: UUID | None,
        event_type: str,
        quantity: float = 1.0,
        metadata: dict[str, Any] | None = None,
    ) -> None: ...


class NoopBillingProvider:
    """Default Mac/local provider — records nothing externally."""

    def report_usage(
        self,
        *,
        tenant_id: UUID | None,
        event_type: str,
        quantity: float = 1.0,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        _ = (tenant_id, event_type, quantity, metadata)
        return None


def get_billing_provider() -> BillingProvider:
    return NoopBillingProvider()
