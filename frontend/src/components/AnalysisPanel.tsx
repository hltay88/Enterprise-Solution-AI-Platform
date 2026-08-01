"use client";

import { useEffect, useState } from "react";

import { apiGet, apiPost, ApiClientError } from "@/lib/api";
import type { AiStatus, AnalysisResult } from "@/lib/types";

type AnalysisPanelProps = {
  projectId: string;
};

type PanelState =
  | { kind: "loading" }
  | { kind: "empty" }
  | { kind: "ready"; analysis: AnalysisResult }
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

function Section({ title, body }: { title: string; body: string | null }) {
  return (
    <div className="analysis-section">
      <h3>{title}</h3>
      <pre>{body?.trim() || "—"}</pre>
    </div>
  );
}

export function AnalysisPanel({ projectId }: AnalysisPanelProps) {
  const [state, setState] = useState<PanelState>({ kind: "loading" });
  const [running, setRunning] = useState(false);
  const [runError, setRunError] = useState<string | null>(null);
  const [aiStatus, setAiStatus] = useState<AiStatus | null>(null);

  async function loadAiStatus() {
    try {
      const status = await apiGet<AiStatus>("/api/ai/status", true);
      setAiStatus(status);
    } catch {
      setAiStatus(null);
    }
  }

  async function loadAnalysis() {
    try {
      const analysis = await apiGet<AnalysisResult>(
        `/api/projects/${projectId}/analysis`,
        true,
      );
      setState({ kind: "ready", analysis });
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
            : "Unable to load analysis",
      });
    }
  }

  useEffect(() => {
    void loadAnalysis();
    void loadAiStatus();
  }, [projectId]);

  async function runAnalysis() {
    setRunning(true);
    setRunError(null);
    try {
      const analysis = await apiPost<AnalysisResult>(
        `/api/projects/${projectId}/analyze`,
        {},
        true,
      );
      setState({ kind: "ready", analysis });
      void loadAiStatus();
    } catch (error) {
      setRunError(
        error instanceof ApiClientError ? error.message : "Analysis failed",
      );
      void loadAiStatus();
    } finally {
      setRunning(false);
    }
  }

  return (
    <section className="panel analysis-panel">
      <div className="panel-heading">
        <div>
          <h2>AI requirement analysis</h2>
          <p className="muted">
            Uses uploaded document text to draft objectives, requirements, assumptions, and risks.
          </p>
        </div>
        <button
          className="btn-primary btn-compact"
          type="button"
          onClick={runAnalysis}
          disabled={running}
        >
          {running ? "Analyzing…" : state.kind === "ready" ? "Re-run analysis" : "Run analysis"}
        </button>
      </div>

      {aiStatus ? (
        <p className={aiStatus.reachable ? "muted" : "form-error"}>
          {aiStatus.detail ||
            (aiStatus.reachable ? "AI provider ready." : "AI provider is not ready.")}
        </p>
      ) : null}

      {runError ? <p className="form-error">{runError}</p> : null}

      {state.kind === "loading" ? <p className="status">Loading analysis…</p> : null}
      {state.kind === "error" ? (
        <p className="status status-error">{state.message}</p>
      ) : null}
      {state.kind === "empty" ? (
        <div className="empty-state">
          <p>No analysis yet.</p>
          <p className="muted">
            Upload at least one requirement document, then run analysis. With
            ATLAS_AI_PROVIDER=auto, OpenAI is used when available and a local fallback runs if
            quota is exceeded.
          </p>
        </div>
      ) : null}

      {state.kind === "ready" ? (
        <div className="analysis-results">
          <p className="muted">Generated {formatDate(state.analysis.created_at)}</p>
          <Section title="Business objectives" body={state.analysis.business_objectives} />
          <Section
            title="Functional requirements"
            body={state.analysis.functional_requirements}
          />
          <Section
            title="Non-functional requirements"
            body={state.analysis.non_functional_requirements}
          />
          <Section title="Assumptions" body={state.analysis.assumptions} />
          <Section title="Risks" body={state.analysis.risks} />
        </div>
      ) : null}
    </section>
  );
}
