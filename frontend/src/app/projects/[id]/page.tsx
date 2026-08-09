"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { AnalysisPanel } from "@/components/AnalysisPanel";
import { ArchitectureComparePanel } from "@/components/ArchitectureComparePanel";
import { ArchitecturePanel } from "@/components/ArchitecturePanel";
import { BomValidationPanel } from "@/components/BomValidationPanel";
import { AppHeader } from "@/components/AppHeader";
import { AuditLogPanel } from "@/components/AuditLogPanel";
import { ClarificationPanel } from "@/components/ClarificationPanel";
import { DocumentUploadPanel } from "@/components/DocumentUploadPanel";
import { GapAnalysisPanel } from "@/components/GapAnalysisPanel";
import { ProjectForm } from "@/components/ProjectForm";
import { RequireAuth } from "@/components/RequireAuth";
import { RkmGovernancePanel } from "@/components/RkmGovernancePanel";
import { RkmPanel } from "@/components/RkmPanel";
import { SolutionDomainPanel } from "@/components/SolutionDomainPanel";
import { apiDelete, apiGet, apiPut, ApiClientError } from "@/lib/api";
import type { ProjectInput, ProjectSummary } from "@/lib/types";

type DetailState =
  | { kind: "loading" }
  | { kind: "ready"; project: ProjectSummary }
  | { kind: "error"; message: string };

function ProjectDetailContent({ userName }: { userName: string }) {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const projectId = params.id;
  const [state, setState] = useState<DetailState>({ kind: "loading" });
  const [deleting, setDeleting] = useState(false);
  const [rkmRefreshToken, setRkmRefreshToken] = useState(0);
  const [rkmHighlightVersion, setRkmHighlightVersion] = useState<string | null>(
    null,
  );

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const project = await apiGet<ProjectSummary>(`/api/projects/${projectId}`, true);
        if (!cancelled) setState({ kind: "ready", project });
      } catch (error) {
        if (cancelled) return;
        setState({
          kind: "error",
          message:
            error instanceof ApiClientError ? error.message : "Unable to load project",
        });
      }
    }

    void load();
    return () => {
      cancelled = true;
    };
  }, [projectId]);

  async function handleUpdate(values: ProjectInput) {
    try {
      const project = await apiPut<ProjectSummary>(
        `/api/projects/${projectId}`,
        values,
        true,
      );
      setState({ kind: "ready", project });
    } catch (error) {
      throw new Error(
        error instanceof ApiClientError ? error.message : "Unable to update project",
      );
    }
  }

  async function handleDelete() {
    if (!window.confirm("Delete this project? This cannot be undone.")) {
      return;
    }
    setDeleting(true);
    try {
      await apiDelete(`/api/projects/${projectId}`, true);
      router.replace("/dashboard");
    } catch (error) {
      setDeleting(false);
      setState({
        kind: "error",
        message:
          error instanceof ApiClientError ? error.message : "Unable to delete project",
      });
    }
  }

  return (
    <div className="shell">
      <AppHeader userName={userName} />
      <main className="page">
        <section className="page-header">
          <p className="muted">
            <Link href="/dashboard">← Back to dashboard</Link>
          </p>
          <h1>Project details</h1>
          <p>
            Update sales intake, upload documents, generate a Draft RKM, run gap analysis,
            answer clarifications, then approve and publish.
          </p>
        </section>

        {state.kind === "loading" ? <p className="status">Loading project…</p> : null}
        {state.kind === "error" ? (
          <p className="status status-error">{state.message}</p>
        ) : null}

        {state.kind === "ready" ? (
          <>
            <section className="form-panel">
              <ProjectForm
                initial={state.project}
                submitLabel="Save changes"
                onSubmit={handleUpdate}
              />
            </section>

            <DocumentUploadPanel projectId={projectId} />
            <RkmPanel
              projectId={projectId}
              refreshToken={rkmRefreshToken}
              highlightVersion={rkmHighlightVersion}
            />
            <GapAnalysisPanel
              projectId={projectId}
              onDraftUpdated={(versionLabel) => {
                setRkmRefreshToken((value) => value + 1);
                setRkmHighlightVersion(versionLabel || null);
              }}
            />
            <RkmGovernancePanel
              projectId={projectId}
              refreshToken={rkmRefreshToken}
              onDraftUpdated={(versionLabel) => {
                setRkmRefreshToken((value) => value + 1);
                setRkmHighlightVersion(versionLabel || null);
              }}
            />
            <SolutionDomainPanel
              projectId={projectId}
              refreshToken={rkmRefreshToken}
            />
            <ArchitecturePanel
              projectId={projectId}
              refreshToken={rkmRefreshToken}
            />
            <ArchitectureComparePanel
              projectId={projectId}
              refreshToken={rkmRefreshToken}
            />
            <BomValidationPanel
              projectId={projectId}
              refreshToken={rkmRefreshToken}
            />
            <AnalysisPanel projectId={projectId} />
            <ClarificationPanel projectId={projectId} />
            <AuditLogPanel projectId={projectId} refreshToken={rkmRefreshToken} />

            <section className="form-panel">
              <div className="danger-zone">
                <button
                  className="btn-secondary"
                  type="button"
                  onClick={handleDelete}
                  disabled={deleting}
                >
                  {deleting ? "Deleting…" : "Delete project"}
                </button>
              </div>
            </section>
          </>
        ) : null}
      </main>
    </div>
  );
}

export default function ProjectDetailPage() {
  return (
    <RequireAuth>
      {(user) => <ProjectDetailContent userName={user.name} />}
    </RequireAuth>
  );
}
