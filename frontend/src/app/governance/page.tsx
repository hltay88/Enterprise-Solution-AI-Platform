"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { AppHeader } from "@/components/AppHeader";
import { RequireAuth } from "@/components/RequireAuth";
import { apiGet, ApiClientError } from "@/lib/api";
import type { AuditEvent, UsageSummary } from "@/lib/types";

function GovernanceContent({ userName }: { userName: string }) {
  const [usage, setUsage] = useState<UsageSummary | null>(null);
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const [summary, audit] = await Promise.all([
          apiGet<UsageSummary>("/api/v1/usage/summary", true),
          apiGet<AuditEvent[]>("/api/v1/audit-events?limit=40", true),
        ]);
        if (!cancelled) {
          setUsage(summary);
          setEvents(audit);
        }
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof ApiClientError
              ? err.message
              : "Unable to load governance data (approver role required)",
          );
        }
      }
    }
    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="shell">
      <AppHeader userName={userName} showDashboardLink showKnowledgeLink />
      <main className="page">
        <section className="page-header">
          <p className="muted">
            <Link href="/dashboard">← Back to dashboard</Link>
          </p>
          <h1>Governance</h1>
          <p>
            Sprint 5.4 — usage summary and consolidated audit events (approver).
          </p>
        </section>

        {error ? <p className="status status-error">{error}</p> : null}

        {usage ? (
          <section className="panel rkm-panel">
            <h2>Usage summary</h2>
            <p>
              Total {usage.total} · success {usage.success_count} · failure{" "}
              {usage.failure_count}
              {usage.avg_latency_ms != null
                ? ` · avg latency ${Math.round(usage.avg_latency_ms)}ms`
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
          <h2>Audit events</h2>
          {events.length === 0 ? (
            <p className="muted">No audit events yet.</p>
          ) : (
            <ul>
              {events.map((e) => (
                <li key={e.id}>
                  <span className="muted">
                    {new Date(e.created_at).toLocaleString()} · {e.action}
                  </span>{" "}
                  — {e.summary}
                </li>
              ))}
            </ul>
          )}
        </section>
      </main>
    </div>
  );
}

export default function GovernancePage() {
  return (
    <RequireAuth>
      {(user) => <GovernanceContent userName={user.name} />}
    </RequireAuth>
  );
}
