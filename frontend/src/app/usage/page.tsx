"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { AppHeader } from "@/components/AppHeader";
import { RequireAuth } from "@/components/RequireAuth";
import { apiGet, ApiClientError } from "@/lib/api";
import type { UsageRecord, UsageSummary } from "@/lib/types";

function UsageDashboardContent({ userName }: { userName: string }) {
  const [usage, setUsage] = useState<UsageSummary | null>(null);
  const [records, setRecords] = useState<UsageRecord[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const [summary, list] = await Promise.all([
          apiGet<UsageSummary>("/api/v1/usage/summary", true),
          apiGet<UsageRecord[]>("/api/v1/usage?limit=40", true),
        ]);
        if (!cancelled) {
          setUsage(summary);
          setRecords(list);
        }
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof ApiClientError
              ? err.message
              : "Unable to load usage dashboard (approver role required)",
          );
        }
      }
    }
    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  const estimatedTotal = records.reduce(
    (sum, row) => sum + (row.estimated_cost_usd ?? 0),
    0,
  );

  return (
    <div className="shell">
      <AppHeader userName={userName} showDashboardLink showKnowledgeLink />
      <main className="page">
        <section className="page-header">
          <p className="muted">
            <Link href="/governance">← Governance / audit</Link>
          </p>
          <h1>Usage Dashboard</h1>
          <p>
            Metered usage observability — latency, event mix, and estimated cost
            (portable Phase 5 billing).
          </p>
        </section>

        {error ? <p className="status status-error">{error}</p> : null}

        {usage ? (
          <section className="panel rkm-panel">
            <h2>Summary</h2>
            <p>
              Total {usage.total} · success {usage.success_count} · failure{" "}
              {usage.failure_count}
              {usage.avg_latency_ms != null
                ? ` · avg latency ${Math.round(usage.avg_latency_ms)}ms`
                : ""}
              {estimatedTotal > 0
                ? ` · est. cost (recent) $${estimatedTotal.toFixed(4)}`
                : ""}
            </p>
            <ul>
              {Object.entries(usage.by_event_type).map(([k, v]) => (
                <li key={k}>
                  {k}: {v}
                </li>
              ))}
            </ul>
          </section>
        ) : null}

        <section className="panel rkm-panel">
          <h2>Recent usage records</h2>
          {records.length === 0 ? (
            <p className="muted">No usage records yet.</p>
          ) : (
            <ul>
              {records.map((row) => (
                <li key={row.id}>
                  <span className="muted">
                    {new Date(row.created_at).toLocaleString()} · {row.event_type}
                  </span>
                  {row.latency_ms != null ? ` · ${row.latency_ms}ms` : ""}
                  {row.estimated_cost_usd != null
                    ? ` · $${row.estimated_cost_usd.toFixed(4)}`
                    : ""}
                  {row.success ? "" : " · failed"}
                </li>
              ))}
            </ul>
          )}
        </section>
      </main>
    </div>
  );
}

export default function UsageDashboardPage() {
  return (
    <RequireAuth>
      {(user) => <UsageDashboardContent userName={user.name} />}
    </RequireAuth>
  );
}
