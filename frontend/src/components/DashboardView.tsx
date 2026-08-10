"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { apiGet, ApiClientError } from "@/lib/api";
import type { ProjectSummary, UserPublic } from "@/lib/types";
import { AppHeader } from "@/components/AppHeader";

type DashboardViewProps = {
  user: UserPublic;
};

type ListState =
  | { kind: "loading" }
  | { kind: "ready"; projects: ProjectSummary[] }
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

export function DashboardView({ user }: DashboardViewProps) {
  const [state, setState] = useState<ListState>({ kind: "loading" });

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const projects = await apiGet<ProjectSummary[]>("/api/projects", true);
        if (!cancelled) setState({ kind: "ready", projects });
      } catch (error) {
        if (cancelled) return;
        setState({
          kind: "error",
          message:
            error instanceof ApiClientError
              ? error.message
              : "Unable to load projects",
        });
      }
    }

    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="shell">
      <AppHeader userName={user.name} />
      <main className="page">
        <section className="page-header">
          <h1>Dashboard</h1>
          <p>
            Welcome back, {user.name}. Your saved project history is listed below.
          </p>
        </section>

        <section className="panel">
          <div className="panel-heading">
            <h2>Project history</h2>
            <div className="button-row">
              <Link className="btn-secondary btn-compact" href="/knowledge">
                Knowledge Library
              </Link>
              <Link className="btn-primary btn-compact" href="/projects/new">
                New project
              </Link>
            </div>
          </div>

          {state.kind === "loading" ? (
            <p className="status">Loading projects…</p>
          ) : null}

          {state.kind === "error" ? (
            <p className="status status-error">{state.message}</p>
          ) : null}

          {state.kind === "ready" && state.projects.length === 0 ? (
            <div className="empty-state">
              <p>No projects yet.</p>
              <p className="muted">
                Create your first project to begin capturing customer requirements.
              </p>
              <Link className="btn-primary" href="/projects/new">
                Create project
              </Link>
            </div>
          ) : null}

          {state.kind === "ready" && state.projects.length > 0 ? (
            <div className="table-wrap">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Project</th>
                    <th>Customer</th>
                    <th>Request type</th>
                    <th>Deal</th>
                    <th>Status</th>
                    <th>Updated</th>
                  </tr>
                </thead>
                <tbody>
                  {state.projects.map((project) => (
                    <tr key={project.id}>
                      <td>
                        <Link className="table-link" href={`/projects/${project.id}`}>
                          {project.project_name}
                        </Link>
                      </td>
                      <td>{project.customer || "—"}</td>
                      <td>{project.request_type || "—"}</td>
                      <td>{project.deal_name || project.deal_id || "—"}</td>
                      <td>
                        <span className="status-pill">{project.status}</span>
                      </td>
                      <td>{formatDate(project.updated_at)}</td>
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
