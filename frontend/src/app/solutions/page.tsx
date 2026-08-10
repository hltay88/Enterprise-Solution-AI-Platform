"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { AppHeader } from "@/components/AppHeader";
import { RequireAuth } from "@/components/RequireAuth";
import { apiGet, ApiClientError } from "@/lib/api";
import type { ProjectSummary } from "@/lib/types";

function SolutionReviewContent({ userName }: { userName: string }) {
  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const rows = await apiGet<ProjectSummary[]>("/api/projects", true);
        if (!cancelled) setProjects(rows);
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof ApiClientError
              ? err.message
              : "Unable to load projects for solution review",
          );
        }
      } finally {
        if (!cancelled) setLoading(false);
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
          <h1>Solution Review</h1>
          <p>
            Review projects for RKM, architecture, specialist advisory, and
            collaboration readiness (Phase 5 UI).
          </p>
        </section>

        {error ? <p className="status status-error">{error}</p> : null}
        {loading ? <p className="status">Loading projects…</p> : null}

        {!loading && projects.length === 0 ? (
          <section className="panel">
            <p>No projects yet.</p>
            <Link className="btn-primary" href="/projects/new">
              Create project
            </Link>
          </section>
        ) : null}

        <section className="panel">
          <div className="panel-heading">
            <h2>Projects</h2>
            <Link className="btn-secondary btn-compact" href="/approvals">
              Approval Center
            </Link>
          </div>
          {projects.length > 0 ? (
            <div className="table-wrap">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Project</th>
                    <th>Customer</th>
                    <th>Status</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {projects.map((p) => (
                    <tr key={p.id}>
                      <td>
                        <Link className="table-link" href={`/projects/${p.id}`}>
                          {p.project_name}
                        </Link>
                      </td>
                      <td>{p.customer || "—"}</td>
                      <td>
                        <span className="status-pill">{p.status}</span>
                      </td>
                      <td>
                        <div className="button-row">
                          <Link
                            className="btn-secondary btn-compact"
                            href={`/projects/${p.id}#agent-workspace-panel`}
                          >
                            Agents
                          </Link>
                          <Link
                            className="btn-secondary btn-compact"
                            href={`/projects/${p.id}#collaboration-panel`}
                          >
                            Collaboration
                          </Link>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : null}
        </section>
      </main>
    </div>
  );
}

export default function SolutionReviewPage() {
  return (
    <RequireAuth>
      {(user) => <SolutionReviewContent userName={user.name} />}
    </RequireAuth>
  );
}
