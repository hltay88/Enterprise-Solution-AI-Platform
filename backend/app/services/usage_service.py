"""Sprint 5.4 — usage recording helpers."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.collaboration import UsageRecord
from app.schemas.collaboration import UsageRecordOut, UsageSummaryOut
from app.services.billing import get_billing_provider


class UsageService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.billing = get_billing_provider(db)

    def record(
        self,
        *,
        event_type: str,
        user_id: UUID | None = None,
        project_id: UUID | None = None,
        tenant_id: UUID | None = None,
        provider: str | None = None,
        model: str | None = None,
        latency_ms: int | None = None,
        token_input: int | None = None,
        token_output: int | None = None,
        estimated_cost_usd: float | None = None,
        success: bool = True,
        error_code: str | None = None,
        metadata: dict[str, Any] | None = None,
        commit: bool = True,
        quantity: float = 1.0,
    ) -> UsageRecord:
        cost = estimated_cost_usd
        if cost is None:
            cost = self.billing.estimate_cost_usd(event_type=event_type, quantity=quantity)
        self.billing.report_usage(
            tenant_id=tenant_id,
            event_type=event_type,
            quantity=quantity,
            metadata=metadata,
        )
        row = UsageRecord(
            event_type=event_type,
            provider=provider,
            model=model,
            latency_ms=latency_ms,
            token_input=token_input,
            token_output=token_output,
            estimated_cost_usd=cost,
            success=success,
            error_code=error_code,
            user_id=user_id,
            project_id=project_id,
            tenant_id=tenant_id,
            metadata_json=metadata or {},
        )
        self.db.add(row)
        if commit:
            self.db.commit()
            self.db.refresh(row)
        else:
            self.db.flush()
        return row

    def list_records(
        self,
        *,
        project_id: UUID | None = None,
        event_type: str | None = None,
        tenant_id: UUID | None = None,
        limit: int = 100,
    ) -> list[UsageRecordOut]:
        statement = select(UsageRecord).order_by(UsageRecord.created_at.desc())
        if project_id is not None:
            statement = statement.where(UsageRecord.project_id == project_id)
        if event_type:
            statement = statement.where(UsageRecord.event_type == event_type)
        if tenant_id is not None:
            statement = statement.where(
                (UsageRecord.tenant_id == tenant_id) | (UsageRecord.tenant_id.is_(None)),
            )
        statement = statement.limit(max(1, min(limit, 500)))
        rows = list(self.db.scalars(statement).all())
        return [self._to_out(row) for row in rows]

    def summary(
        self,
        *,
        project_id: UUID | None = None,
        tenant_id: UUID | None = None,
        limit_scan: int = 1000,
    ) -> UsageSummaryOut:
        statement = select(UsageRecord).order_by(UsageRecord.created_at.desc()).limit(limit_scan)
        if project_id is not None:
            statement = statement.where(UsageRecord.project_id == project_id)
        if tenant_id is not None:
            statement = statement.where(
                (UsageRecord.tenant_id == tenant_id) | (UsageRecord.tenant_id.is_(None)),
            )
        rows = list(self.db.scalars(statement).all())
        by_type: dict[str, int] = {}
        success_count = 0
        latencies: list[int] = []
        for row in rows:
            by_type[row.event_type] = by_type.get(row.event_type, 0) + 1
            if row.success:
                success_count += 1
            if row.latency_ms is not None:
                latencies.append(row.latency_ms)
        avg = (sum(latencies) / len(latencies)) if latencies else None
        return UsageSummaryOut(
            total=len(rows),
            success_count=success_count,
            failure_count=len(rows) - success_count,
            by_event_type=by_type,
            avg_latency_ms=avg,
        )

    @staticmethod
    def _to_out(row: UsageRecord) -> UsageRecordOut:
        return UsageRecordOut(
            id=row.id,
            event_type=row.event_type,
            provider=row.provider,
            model=row.model,
            latency_ms=row.latency_ms,
            token_input=row.token_input,
            token_output=row.token_output,
            estimated_cost_usd=row.estimated_cost_usd,
            success=row.success,
            error_code=row.error_code,
            user_id=row.user_id,
            project_id=row.project_id,
            tenant_id=row.tenant_id,
            metadata=row.metadata_json if isinstance(row.metadata_json, dict) else {},
            created_at=row.created_at,
        )
