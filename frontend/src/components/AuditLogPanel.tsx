"use client";

import { useEffect, useState } from "react";

import { apiGet, ApiClientError } from "@/lib/api";
import type { AuditLogEntry } from "@/lib/types";

type AuditLogPanelProps = {
  projectId: string;
  refreshToken?: number;
};

type PanelState =
  | { kind: "loading" }
  | { kind: "ready"; rows: AuditLogEntry[] }
  | { kind: "error"; message: string };

function formatDate(value: string): string {
  try {
    return new Intl.DateTimeFormat(undefined, {
      dateStyle: "medium",
      timeStyle: "short",
    }).format(new Date(value));
  } catch {
    return value;
  }
}

export function AuditLogPanel({
  projectId,
  refreshToken = 0,
}: AuditLogPanelProps) {
  const [state, setState] = useState<PanelState>({ kind: "loading" });

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const rows = await apiGet<AuditLogEntry[]>(
          `/api/v1/projects/${projectId}/audit-logs?limit=50`,
          true,
        );
        if (!cancelled) setState({ kind: "ready", rows });
      } catch (err) {
        if (cancelled) return;
        setState({
          kind: "error",
          message:
            err instanceof ApiClientError
              ? err.message
              : "Unable to load audit log",
        });
      }
    }
    void load();
    return () => {
      cancelled = true;
    };
  }, [projectId, refreshToken]);

  return (
    <section className="panel rkm-panel" id="audit-log-panel">
      <div className="panel-heading">
        <div>
          <h2>Audit log</h2>
          <p className="muted">
            Upload, review, approve, and publish events for this project (Stage F)
          </p>
        </div>
      </div>

      {state.kind === "loading" ? <p className="status">Loading audit log…</p> : null}
      {state.kind === "error" ? (
        <p className="status status-error">{state.message}</p>
      ) : null}
      {state.kind === "ready" && state.rows.length === 0 ? (
        <p className="muted">No audit events yet.</p>
      ) : null}
      {state.kind === "ready" && state.rows.length > 0 ? (
        <ul className="rkm-list">
          {state.rows.map((row) => (
            <li key={row.id} className="rkm-item">
              <div className="rkm-item-head">
                <strong>{row.action}</strong>
                <span className="muted">{formatDate(row.created_at)}</span>
              </div>
              <p>{row.summary}</p>
            </li>
          ))}
        </ul>
      ) : null}
    </section>
  );
}
