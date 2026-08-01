"use client";

import { useEffect, useState } from "react";

import { apiGet, apiPost, ApiClientError } from "@/lib/api";
import type { ClarificationQuestion } from "@/lib/types";

type ClarificationPanelProps = {
  projectId: string;
};

type PanelState =
  | { kind: "loading" }
  | { kind: "empty" }
  | { kind: "ready"; questions: ClarificationQuestion[] }
  | { kind: "error"; message: string };

export function ClarificationPanel({ projectId }: ClarificationPanelProps) {
  const [state, setState] = useState<PanelState>({ kind: "loading" });
  const [running, setRunning] = useState(false);
  const [runError, setRunError] = useState<string | null>(null);

  async function loadQuestions() {
    try {
      const questions = await apiGet<ClarificationQuestion[]>(
        `/api/projects/${projectId}/clarifications`,
        true,
      );
      if (questions.length === 0) {
        setState({ kind: "empty" });
      } else {
        setState({ kind: "ready", questions });
      }
    } catch (error) {
      setState({
        kind: "error",
        message:
          error instanceof ApiClientError
            ? error.message
            : "Unable to load clarification questions",
      });
    }
  }

  useEffect(() => {
    void loadQuestions();
  }, [projectId]);

  async function generateQuestions() {
    setRunning(true);
    setRunError(null);
    try {
      const questions = await apiPost<ClarificationQuestion[]>(
        `/api/projects/${projectId}/clarification`,
        {},
        true,
      );
      setState(
        questions.length === 0
          ? { kind: "empty" }
          : { kind: "ready", questions },
      );
    } catch (error) {
      setRunError(
        error instanceof ApiClientError
          ? error.message
          : "Failed to generate clarification questions",
      );
    } finally {
      setRunning(false);
    }
  }

  return (
    <section className="panel clarification-panel">
      <div className="panel-heading">
        <div>
          <h2>Clarification questions</h2>
          <p className="muted">
            Generated from the latest requirement analysis to close gaps before solution design.
          </p>
        </div>
        <button
          className="btn-primary btn-compact"
          type="button"
          onClick={generateQuestions}
          disabled={running}
        >
          {running
            ? "Generating…"
            : state.kind === "ready"
              ? "Regenerate questions"
              : "Generate questions"}
        </button>
      </div>

      {runError ? <p className="form-error">{runError}</p> : null}

      {state.kind === "loading" ? (
        <p className="status">Loading clarification questions…</p>
      ) : null}
      {state.kind === "error" ? (
        <p className="status status-error">{state.message}</p>
      ) : null}
      {state.kind === "empty" ? (
        <div className="empty-state">
          <p>No clarification questions yet.</p>
          <p className="muted">
            Run AI requirement analysis first, then generate clarification questions.
          </p>
        </div>
      ) : null}

      {state.kind === "ready" ? (
        <ol className="clarification-list">
          {state.questions.map((item) => (
            <li key={item.id}>
              <span className="status-pill">{item.status}</span>
              <p>{item.question}</p>
            </li>
          ))}
        </ol>
      ) : null}
    </section>
  );
}
