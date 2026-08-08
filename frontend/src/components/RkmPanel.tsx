"use client";

import { useEffect, useRef, useState } from "react";

import { apiGet, apiPost, ApiClientError } from "@/lib/api";
import type {
  JobStatus,
  RkmAnalyzeAccepted,
  RkmDraft,
  RkmEvidence,
  RkmRequirement,
  RkmVersionSummary,
} from "@/lib/types";

type RkmPanelProps = {
  projectId: string;
};

type PanelState =
  | { kind: "loading" }
  | { kind: "empty" }
  | { kind: "ready"; rkm: RkmDraft }
  | { kind: "error"; message: string };

const POLL_MS = 1500;

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

function evidenceLabel(evidence: RkmEvidence | undefined): string {
  if (!evidence) return "Evidence";
  if (evidence.source_type === "sales_intake") {
    return `Sales intake${evidence.field_name ? `: ${evidence.field_name}` : ""}`;
  }
  if (evidence.source_type === "document") {
    return evidence.note || "Document excerpt";
  }
  return evidence.source_type;
}

function RequirementList({
  title,
  items,
  evidenceMap,
}: {
  title: string;
  items: RkmRequirement[];
  evidenceMap: Map<string, RkmEvidence>;
}) {
  if (!items.length) return null;
  return (
    <div className="rkm-section">
      <h3>{title}</h3>
      <ul className="rkm-list">
        {items.map((item) => (
          <li key={item.id} className="rkm-item">
            <div className="rkm-item-head">
              <strong>{item.title}</strong>
              <span className="muted">
                {(item.category || "uncategorized").replaceAll("_", " ")}
                {" · "}
                {item.priority}
                {" · "}
                conf {Math.round(item.confidence)}
              </span>
            </div>
            <p>{item.description}</p>
            <div className="rkm-evidence">
              {item.evidence_ids.map((id) => {
                const evidence = evidenceMap.get(id);
                return (
                  <details key={id} className="rkm-evidence-chip">
                    <summary>{evidenceLabel(evidence)}</summary>
                    <p className="muted">
                      {evidence?.excerpt || "No excerpt"}
                    </p>
                  </details>
                );
              })}
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}

export function RkmPanel({ projectId }: RkmPanelProps) {
  const [state, setState] = useState<PanelState>({ kind: "loading" });
  const [running, setRunning] = useState(false);
  const [runError, setRunError] = useState<string | null>(null);
  const [jobProgress, setJobProgress] = useState<number | null>(null);
  const [versions, setVersions] = useState<RkmVersionSummary[]>([]);
  const pollTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  function clearPoll() {
    if (pollTimer.current) {
      clearTimeout(pollTimer.current);
      pollTimer.current = null;
    }
  }

  async function loadDraft() {
    try {
      const rkm = await apiGet<RkmDraft>(
        `/api/v1/projects/${projectId}/requirements?status=draft`,
        true,
      );
      setState({ kind: "ready", rkm });
    } catch (error) {
      if (error instanceof ApiClientError && error.status === 404) {
        setState({ kind: "empty" });
        return;
      }
      setState({
        kind: "error",
        message:
          error instanceof ApiClientError
            ? error.message
            : "Unable to load Draft RKM",
      });
    }
  }

  async function loadVersions() {
    try {
      const rows = await apiGet<RkmVersionSummary[]>(
        `/api/v1/projects/${projectId}/requirements/versions`,
        true,
      );
      setVersions(rows);
    } catch {
      setVersions([]);
    }
  }

  async function pollJob(jobId: string) {
    clearPoll();
    try {
      const job = await apiGet<JobStatus>(`/api/v1/jobs/${jobId}`, true);
      setJobProgress(job.progress);
      if (job.status === "queued" || job.status === "processing") {
        pollTimer.current = setTimeout(() => {
          void pollJob(jobId);
        }, POLL_MS);
        return;
      }
      if (job.status === "failed") {
        setRunError(job.error_message || "RKM generation failed");
        setRunning(false);
        setJobProgress(null);
        await loadDraft();
        return;
      }
      setRunning(false);
      setJobProgress(null);
      await loadDraft();
      await loadVersions();
    } catch (error) {
      setRunning(false);
      setJobProgress(null);
      setRunError(
        error instanceof ApiClientError
          ? error.message
          : "Unable to poll RKM job",
      );
    }
  }

  useEffect(() => {
    void loadDraft();
    void loadVersions();
    return () => clearPoll();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId]);

  async function generateDraft() {
    setRunning(true);
    setRunError(null);
    setJobProgress(0);
    try {
      const accepted = await apiPost<RkmAnalyzeAccepted>(
        `/api/v1/projects/${projectId}/requirements/analyze`,
        {},
        true,
      );
      void pollJob(accepted.job_id);
    } catch (error) {
      setRunning(false);
      setJobProgress(null);
      setRunError(
        error instanceof ApiClientError
          ? error.message
          : "Unable to start RKM generation",
      );
    }
  }

  const evidenceMap =
    state.kind === "ready"
      ? new Map(state.rkm.evidence.map((item) => [item.id, item]))
      : new Map<string, RkmEvidence>();

  return (
    <section className="panel rkm-panel">
      <div className="panel-heading">
        <div>
          <h2>Draft Requirement Knowledge Model</h2>
          <p className="muted">
            Structured requirements with evidence links from sales intake and
            documents (Stage C)
          </p>
        </div>
        <button
          className="btn-primary btn-compact"
          type="button"
          onClick={() => void generateDraft()}
          disabled={running}
        >
          {running
            ? jobProgress != null
              ? `Generating… ${jobProgress}%`
              : "Generating…"
            : state.kind === "ready"
              ? "Regenerate Draft RKM"
              : "Generate Draft RKM"}
        </button>
      </div>

      {runError ? <p className="form-error">{runError}</p> : null}

      {state.kind === "loading" ? <p className="status">Loading Draft RKM…</p> : null}
      {state.kind === "empty" ? (
        <div className="empty-state">
          <p>No Draft RKM yet.</p>
          <p className="muted">
            Save sales intake and upload documents, then generate a Draft RKM.
          </p>
        </div>
      ) : null}
      {state.kind === "error" ? (
        <p className="status status-error">{state.message}</p>
      ) : null}

      {state.kind === "ready" ? (
        <>
          <div className="rkm-meta muted">
            <span>Version {state.rkm.version.number}</span>
            <span> · {state.rkm.approval.status.replaceAll("_", " ")}</span>
            <span> · Updated {formatDate(state.rkm.version.updated_at)}</span>
            {state.rkm.analysis.model ? (
              <span> · Model {state.rkm.analysis.model}</span>
            ) : null}
          </div>

          <div className="rkm-scores">
            <span>Completeness {Math.round(state.rkm.analysis.completeness_score)}%</span>
            <span>Confidence {Math.round(state.rkm.analysis.confidence_score)}%</span>
            <span>Evidence coverage {Math.round(state.rkm.analysis.evidence_coverage)}%</span>
          </div>

          {state.rkm.analysis.reasoning_summary ? (
            <p className="rkm-reasoning">{state.rkm.analysis.reasoning_summary}</p>
          ) : null}

          <RequirementList
            title="Business objectives"
            items={state.rkm.business_objectives}
            evidenceMap={evidenceMap}
          />
          {state.rkm.current_environment?.summary ||
          (state.rkm.current_environment?.items?.length ?? 0) > 0 ? (
            <div className="rkm-section">
              <h3>Current environment</h3>
              {state.rkm.current_environment.summary ? (
                <p>{state.rkm.current_environment.summary}</p>
              ) : null}
              <ul className="rkm-list">
                {(state.rkm.current_environment.items || []).map((item) => (
                  <li key={item.id} className="rkm-item">
                    <strong>{item.title}</strong>
                    <p>{item.description}</p>
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
          <RequirementList
            title="Functional requirements"
            items={state.rkm.functional_requirements}
            evidenceMap={evidenceMap}
          />
          <RequirementList
            title="Non-functional requirements"
            items={state.rkm.non_functional_requirements}
            evidenceMap={evidenceMap}
          />
          <RequirementList
            title="Constraints"
            items={state.rkm.constraints}
            evidenceMap={evidenceMap}
          />
          <RequirementList
            title="Dependencies"
            items={state.rkm.dependencies}
            evidenceMap={evidenceMap}
          />
          <RequirementList
            title="Risks"
            items={state.rkm.risks}
            evidenceMap={evidenceMap}
          />
          <RequirementList
            title="Assumptions"
            items={state.rkm.assumptions}
            evidenceMap={evidenceMap}
          />

          {state.rkm.stakeholders.length > 0 ? (
            <div className="rkm-section">
              <h3>Stakeholders</h3>
              <ul className="rkm-list">
                {state.rkm.stakeholders.map((person) => (
                  <li key={person.id} className="rkm-item">
                    <strong>{person.name}</strong>
                    <p className="muted">
                      {[person.role, person.designation, person.contact]
                        .filter(Boolean)
                        .join(" · ")}
                    </p>
                  </li>
                ))}
              </ul>
            </div>
          ) : null}

          {versions.length > 1 ? (
            <div className="rkm-section">
              <h3>Version history</h3>
              <ul className="rkm-list">
                {versions.map((version) => (
                  <li key={version.id} className="muted">
                    v{version.version_label}
                    {version.is_active_draft ? " (active draft)" : ""}
                    {" · "}
                    {formatDate(version.updated_at)}
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
        </>
      ) : null}
    </section>
  );
}
