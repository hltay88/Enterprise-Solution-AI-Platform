"use client";

import { useEffect, useState } from "react";

import { apiGet, apiPost, ApiClientError } from "@/lib/api";
import type {
  DomainAnalysis,
  DomainOpenQuestion,
  DomainTraceabilityRow,
  SolutionDomain,
} from "@/lib/types";

type SolutionDomainPanelProps = {
  projectId: string;
  refreshToken?: number;
};

type PanelState =
  | { kind: "loading" }
  | { kind: "empty" }
  | { kind: "ready"; analysis: DomainAnalysis }
  | { kind: "error"; message: string };

function formatConfidence(value: number): string {
  const pct = value > 1 ? value : value * 100;
  return `${Math.round(pct)}%`;
}

function formatStatus(status: string): string {
  return status.replace(/_/g, " ");
}

export function SolutionDomainPanel({
  projectId,
  refreshToken = 0,
}: SolutionDomainPanelProps) {
  const [state, setState] = useState<PanelState>({ kind: "loading" });
  const [running, setRunning] = useState(false);
  const [runError, setRunError] = useState<string | null>(null);

  async function load() {
    try {
      const analysis = await apiGet<DomainAnalysis>(
        `/api/v1/projects/${projectId}/domains`,
        true,
      );
      setState({ kind: "ready", analysis });
    } catch (err) {
      if (err instanceof ApiClientError && err.status === 404) {
        setState({ kind: "empty" });
        return;
      }
      setState({
        kind: "error",
        message:
          err instanceof ApiClientError
            ? err.message
            : "Unable to load solution domains",
      });
    }
  }

  useEffect(() => {
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId, refreshToken]);

  async function analyze() {
    setRunning(true);
    setRunError(null);
    try {
      const analysis = await apiPost<DomainAnalysis>(
        `/api/v1/projects/${projectId}/domains/analyze`,
        {},
        true,
      );
      setState({ kind: "ready", analysis });
    } catch (err) {
      setRunError(
        err instanceof ApiClientError
          ? err.message
          : "Unable to analyze solution domains",
      );
    } finally {
      setRunning(false);
    }
  }

  return (
    <section className="panel rkm-panel" id="solution-domain-panel">
      <div className="panel-heading">
        <div>
          <h2>Solution domain model</h2>
          <p className="muted">
            Phase 3 — identify solution domains from a Published Requirement
            Knowledge Model (before architecture)
          </p>
        </div>
        <button
          className="btn-primary btn-compact"
          type="button"
          onClick={() => void analyze()}
          disabled={running}
        >
          {running
            ? "Analyzing…"
            : state.kind === "ready"
              ? "Re-analyze domains"
              : "Analyze domains"}
        </button>
      </div>

      {runError ? <p className="form-error">{runError}</p> : null}
      {state.kind === "loading" ? <p className="status">Loading…</p> : null}
      {state.kind === "empty" ? (
        <div className="empty-state">
          <p>No solution domain analysis yet.</p>
          <p className="muted">
            Publish an RKM first (Stage E), then analyze domains here.
          </p>
        </div>
      ) : null}
      {state.kind === "error" ? (
        <p className="status status-error">{state.message}</p>
      ) : null}

      {state.kind === "ready" ? (
        <DomainAnalysisView analysis={state.analysis} />
      ) : null}
    </section>
  );
}

function DomainAnalysisView({ analysis }: { analysis: DomainAnalysis }) {
  return (
    <>
      <div className="rkm-meta muted">
        <span>Domains v{analysis.version_label}</span>
        <span>
          {" "}
          · from Published RKM v{analysis.rkm_version_label || "—"}
        </span>
        {analysis.model ? <span> · Model {analysis.model}</span> : null}
        {analysis.prompt_version ? (
          <span> · Prompt {analysis.prompt_version}</span>
        ) : null}
        {analysis.knowledge_pack_version ? (
          <span> · Pack {analysis.knowledge_pack_version}</span>
        ) : null}
      </div>
      {analysis.summary ? <p>{analysis.summary}</p> : null}
      {analysis.reasoning_summary ? (
        <p className="rkm-reasoning">{analysis.reasoning_summary}</p>
      ) : null}

      <div className="rkm-section">
        <h3>Domains</h3>
        {analysis.domains.length === 0 ? (
          <p className="muted">No domains selected in this analysis.</p>
        ) : (
          <ul className="rkm-list">
            {analysis.domains.map((domain) => (
              <li key={domain.id} className="rkm-item">
                <DomainItem domain={domain} />
              </li>
            ))}
          </ul>
        )}
      </div>

      <OpenQuestionsSection
        title="Analysis open questions"
        questions={analysis.open_questions}
      />

      <TraceabilitySection rows={analysis.traceability} />
    </>
  );
}

function DomainItem({ domain }: { domain: SolutionDomain }) {
  const label = domain.name || domain.domain_code;
  return (
    <>
      <div className="rkm-item-head">
        <strong>
          {label}{" "}
          <span className="muted">({domain.domain_code})</span>
        </strong>
        <span className="muted">
          {domain.mandatory_or_optional} · confidence{" "}
          {formatConfidence(domain.confidence)} · via {domain.selection_source}
        </span>
      </div>
      {domain.reason ? <p>{domain.reason}</p> : null}

      {domain.supporting_requirements.length > 0 ? (
        <div className="rkm-evidence">
          {domain.supporting_requirements.map((reqId) => (
            <span key={reqId} className="rkm-evidence-chip">
              {reqId}
            </span>
          ))}
        </div>
      ) : null}

      {domain.dependencies.length > 0 ? (
        <ul className="rkm-list">
          {domain.dependencies.map((dep, index) => (
            <li
              key={`${dep.depends_on_domain_code}-${index}`}
              className="muted"
            >
              Depends on <strong>{dep.depends_on_domain_code}</strong> (
              {dep.dependency_kind})
              {dep.reason ? ` — ${dep.reason}` : ""}
            </li>
          ))}
        </ul>
      ) : null}

      <OpenQuestionsSection
        title="Open questions"
        questions={domain.open_questions}
      />
    </>
  );
}

function OpenQuestionsSection({
  title,
  questions,
}: {
  title: string;
  questions: DomainOpenQuestion[];
}) {
  if (!questions.length) return null;
  return (
    <div className="rkm-section">
      <h3>{title}</h3>
      <ul className="rkm-list">
        {questions.map((question, index) => (
          <li key={question.id || `${question.question}-${index}`} className="rkm-item">
            <p>{question.question}</p>
            <p className="muted">
              {question.affects_selection
                ? "Affects domain selection"
                : "Informational"}
              {question.domain_code ? ` · ${question.domain_code}` : ""}
              {question.related_requirement_ids.length > 0
                ? ` · ${question.related_requirement_ids.join(", ")}`
                : ""}
            </p>
          </li>
        ))}
      </ul>
    </div>
  );
}

function TraceabilitySection({ rows }: { rows: DomainTraceabilityRow[] }) {
  if (!rows.length) return null;
  return (
    <div className="rkm-section">
      <h3>Requirement → domain traceability</h3>
      <ul className="rkm-list">
        {rows.map((row) => (
          <li key={row.id} className="rkm-item">
            <div className="rkm-item-head">
              <strong>{row.requirement_id}</strong>
              <span className="muted">
                {row.domain_code || "—"} · {formatStatus(row.status)}
              </span>
            </div>
            {row.evidence ? <p className="muted">{row.evidence}</p> : null}
          </li>
        ))}
      </ul>
    </div>
  );
}
