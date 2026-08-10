"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { AppHeader } from "@/components/AppHeader";
import { RequireAuth } from "@/components/RequireAuth";
import { apiGet, apiPost, ApiClientError } from "@/lib/api";
import type { ApprovalRequest, ProjectSummary, ReviewRequest } from "@/lib/types";

type Row = {
  project: ProjectSummary;
  reviews: ReviewRequest[];
  approvals: ApprovalRequest[];
};

function ApprovalCenterContent({ userName }: { userName: string }) {
  const [rows, setRows] = useState<Row[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);

  async function load() {
    setError(null);
    try {
      const projects = await apiGet<ProjectSummary[]>("/api/projects", true);
      const packed = await Promise.all(
        projects.map(async (project) => {
          const [reviews, approvals] = await Promise.all([
            apiGet<ReviewRequest[]>(
              `/api/v1/projects/${project.id}/review-requests`,
              true,
            ),
            apiGet<ApprovalRequest[]>(
              `/api/v1/projects/${project.id}/approval-requests`,
              true,
            ),
          ]);
          return { project, reviews, approvals };
        }),
      );
      setRows(packed);
    } catch (err) {
      setError(
        err instanceof ApiClientError
          ? err.message
          : "Unable to load approval center",
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  const openApprovals = useMemo(
    () =>
      rows.flatMap((row) =>
        row.approvals
          .filter((a) => a.status === "open")
          .map((a) => ({ ...a, project_name: row.project.project_name })),
      ),
    [rows],
  );
  const openReviews = useMemo(
    () =>
      rows.flatMap((row) =>
        row.reviews
          .filter((r) => r.status === "open")
          .map((r) => ({ ...r, project_name: row.project.project_name })),
      ),
    [rows],
  );

  async function resolveApproval(id: string, decision: "approved" | "rejected") {
    setBusy(true);
    try {
      await apiPost(
        `/api/v1/approval-requests/${id}/resolve`,
        { decision, resolution_note: decision },
        true,
      );
      await load();
    } catch (err) {
      setError(
        err instanceof ApiClientError ? err.message : "Resolve approval failed",
      );
    } finally {
      setBusy(false);
    }
  }

  async function completeReview(id: string) {
    setBusy(true);
    try {
      await apiPost(
        `/api/v1/review-requests/${id}/complete`,
        { resolution_note: "Reviewed" },
        true,
      );
      await load();
    } catch (err) {
      setError(
        err instanceof ApiClientError ? err.message : "Complete review failed",
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="shell">
      <AppHeader userName={userName} showDashboardLink showKnowledgeLink />
      <main className="page">
        <section className="page-header">
          <p className="muted">
            <Link href="/dashboard">← Back to dashboard</Link>
          </p>
          <h1>Approval Center</h1>
          <p>
            Cross-project review and approval requests (Phase 5 governance UI).
          </p>
        </section>

        {error ? <p className="status status-error">{error}</p> : null}
        {loading ? <p className="status">Loading requests…</p> : null}

        <section className="panel rkm-panel">
          <h2>Open approval requests ({openApprovals.length})</h2>
          {openApprovals.length === 0 ? (
            <p className="muted">No open approvals.</p>
          ) : (
            <ul>
              {openApprovals.map((a) => (
                <li key={a.id}>
                  <strong>{a.project_name}</strong> · {a.resource_type} —{" "}
                  {a.message || "(no message)"}{" "}
                  <Link href={`/projects/${a.project_id}`}>Open project</Link>{" "}
                  <button
                    type="button"
                    className="btn-primary btn-compact"
                    disabled={busy}
                    onClick={() => void resolveApproval(a.id, "approved")}
                  >
                    Approve
                  </button>{" "}
                  <button
                    type="button"
                    className="btn-secondary btn-compact"
                    disabled={busy}
                    onClick={() => void resolveApproval(a.id, "rejected")}
                  >
                    Reject
                  </button>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="panel rkm-panel">
          <h2>Open review requests ({openReviews.length})</h2>
          {openReviews.length === 0 ? (
            <p className="muted">No open reviews.</p>
          ) : (
            <ul>
              {openReviews.map((r) => (
                <li key={r.id}>
                  <strong>{r.project_name}</strong> · {r.resource_type} —{" "}
                  {r.message || "(no message)"}{" "}
                  <Link href={`/projects/${r.project_id}`}>Open project</Link>{" "}
                  <button
                    type="button"
                    className="btn-secondary btn-compact"
                    disabled={busy}
                    onClick={() => void completeReview(r.id)}
                  >
                    Complete
                  </button>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="panel rkm-panel">
          <h2>All projects</h2>
          <ul>
            {rows.map(({ project, reviews, approvals }) => (
              <li key={project.id}>
                <Link href={`/projects/${project.id}`}>{project.project_name}</Link>
                <span className="muted">
                  {" "}
                  · reviews {reviews.length} · approvals {approvals.length}
                </span>
              </li>
            ))}
          </ul>
        </section>
      </main>
    </div>
  );
}

export default function ApprovalCenterPage() {
  return (
    <RequireAuth>
      {(user) => <ApprovalCenterContent userName={user.name} />}
    </RequireAuth>
  );
}
