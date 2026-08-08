"use client";

import { FormEvent, useEffect, useState } from "react";

import { apiGet, apiPost, ApiClientError } from "@/lib/api";
import type {
  ClarificationAnswerResult,
  GapAnalysisReport,
  RkmClarification,
} from "@/lib/types";

type GapAnalysisPanelProps = {
  projectId: string;
  onDraftUpdated?: () => void;
};

type PanelState =
  | { kind: "loading" }
  | { kind: "idle" }
  | { kind: "ready"; report: GapAnalysisReport }
  | { kind: "error"; message: string };

export function GapAnalysisPanel({
  projectId,
  onDraftUpdated,
}: GapAnalysisPanelProps) {
  const [state, setState] = useState<PanelState>({ kind: "loading" });
  const [questions, setQuestions] = useState<RkmClarification[]>([]);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [running, setRunning] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [note, setNote] = useState<string | null>(null);

  async function loadClarifications() {
    try {
      const items = await apiGet<RkmClarification[]>(
        `/api/v1/projects/${projectId}/clarification`,
        true,
      );
      setQuestions(items);
      if (items.length === 0) {
        setState((prev) => (prev.kind === "ready" ? prev : { kind: "idle" }));
      } else if (state.kind !== "ready") {
        setState({ kind: "idle" });
      }
    } catch (err) {
      if (err instanceof ApiClientError && err.status === 404) {
        setQuestions([]);
        setState({ kind: "idle" });
        return;
      }
      setState({
        kind: "error",
        message:
          err instanceof ApiClientError
            ? err.message
            : "Unable to load clarifications",
      });
    }
  }

  useEffect(() => {
    void loadClarifications();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId]);

  async function runGapAnalysis() {
    setRunning(true);
    setError(null);
    setNote(null);
    try {
      const report = await apiPost<GapAnalysisReport>(
        `/api/v1/projects/${projectId}/requirements/gap-analysis`,
        {},
        true,
      );
      setState({ kind: "ready", report });
      setQuestions(report.clarifications);
      setNote(
        `Gap analysis complete · overall ${Math.round(report.overall_quality)}% (${report.quality_level.replaceAll("_", " ")})`,
      );
      onDraftUpdated?.();
    } catch (err) {
      setError(
        err instanceof ApiClientError
          ? err.message
          : "Gap analysis failed — generate a Draft RKM first",
      );
    } finally {
      setRunning(false);
    }
  }

  async function submitAnswers(event: FormEvent) {
    event.preventDefault();
    const payload = Object.entries(answers)
      .map(([clarification_id, answer]) => ({
        clarification_id,
        answer: answer.trim(),
      }))
      .filter((item) => item.answer.length > 0);

    if (payload.length === 0) {
      setError("Enter at least one clarification answer");
      return;
    }

    setSaving(true);
    setError(null);
    setNote(null);
    try {
      const result = await apiPost<ClarificationAnswerResult>(
        `/api/v1/projects/${projectId}/clarification/answer`,
        { answers: payload },
        true,
      );
      setQuestions(result.clarifications);
      setAnswers({});
      setNote(
        `Saved ${result.answered_count} answer(s) · Draft RKM updated to v${result.version_label}`,
      );
      onDraftUpdated?.();
      // Refresh gap scores against new draft.
      await runGapAnalysis();
    } catch (err) {
      setError(
        err instanceof ApiClientError
          ? err.message
          : "Unable to save clarification answers",
      );
    } finally {
      setSaving(false);
    }
  }

  const openQuestions = questions.filter((q) => q.status !== "answered");
  const answeredQuestions = questions.filter((q) => q.status === "answered");

  return (
    <section className="panel gap-panel">
      <div className="panel-heading">
        <div>
          <h2>Gap analysis & clarifications</h2>
          <p className="muted">
            Deterministic scoring, missing-information gaps, and clarification
            answers that create a new Draft RKM minor version
          </p>
        </div>
        <button
          className="btn-primary btn-compact"
          type="button"
          onClick={() => void runGapAnalysis()}
          disabled={running || saving}
        >
          {running ? "Analyzing…" : "Run gap analysis"}
        </button>
      </div>

      {error ? <p className="form-error">{error}</p> : null}
      {note ? <p className="status">{note}</p> : null}

      {state.kind === "ready" ? (
        <>
          <div className="rkm-scores">
            <span>Completeness {Math.round(state.report.completeness_score)}%</span>
            <span>Confidence {Math.round(state.report.confidence_score)}%</span>
            <span>Evidence {Math.round(state.report.evidence_coverage)}%</span>
            <span>Consistency {Math.round(state.report.consistency_score)}%</span>
            <span>Overall {Math.round(state.report.overall_quality)}%</span>
          </div>

          {state.report.publish_blockers.length > 0 ? (
            <div className="gap-blockers">
              <h3>Publish blockers</h3>
              <ul>
                {state.report.publish_blockers.map((item) => (
                  <li key={item.code}>{item.message}</li>
                ))}
              </ul>
            </div>
          ) : null}

          {state.report.missing_sections.length > 0 ? (
            <p className="muted">
              Missing sections:{" "}
              {state.report.missing_sections
                .map((section) => section.replaceAll("_", " "))
                .join(", ")}
            </p>
          ) : null}

          {state.report.gaps.length > 0 ? (
            <div className="rkm-section">
              <h3>Gaps</h3>
              <ul className="rkm-list">
                {state.report.gaps.slice(0, 12).map((gap) => (
                  <li key={`${gap.code}-${gap.message}`} className="rkm-item">
                    <strong>
                      {gap.severity.toUpperCase()} · {gap.section.replaceAll("_", " ")}
                    </strong>
                    <p>{gap.message}</p>
                  </li>
                ))}
              </ul>
            </div>
          ) : null}

          {state.report.conflicts.length > 0 ? (
            <div className="rkm-section">
              <h3>Conflicts / dependency checks</h3>
              <ul className="rkm-list">
                {state.report.conflicts.map((item) => (
                  <li key={item.code} className="rkm-item">
                    <p>{item.message}</p>
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
        </>
      ) : null}

      {state.kind === "idle" && questions.length === 0 ? (
        <div className="empty-state">
          <p>No gap analysis yet.</p>
          <p className="muted">
            Generate a Draft RKM first, then run gap analysis.
          </p>
        </div>
      ) : null}

      {openQuestions.length > 0 ? (
        <form className="rkm-section" onSubmit={submitAnswers}>
          <h3>Open clarification questions</h3>
          <ul className="rkm-list">
            {openQuestions.map((question) => (
              <li key={question.id} className="rkm-item">
                <div className="rkm-item-head">
                  <strong>{question.question}</strong>
                  <span className="muted">
                    {question.priority} · {question.category}
                  </span>
                </div>
                <p className="muted">{question.reason}</p>
                <textarea
                  className="gap-answer"
                  rows={2}
                  placeholder="Customer answer…"
                  value={answers[question.id] || ""}
                  onChange={(event) =>
                    setAnswers((prev) => ({
                      ...prev,
                      [question.id]: event.target.value,
                    }))
                  }
                />
              </li>
            ))}
          </ul>
          <button
            className="btn-primary btn-compact"
            type="submit"
            disabled={saving || running}
          >
            {saving ? "Saving answers…" : "Submit answers → new RKM version"}
          </button>
        </form>
      ) : null}

      {answeredQuestions.length > 0 ? (
        <div className="rkm-section">
          <h3>Answered</h3>
          <ul className="rkm-list">
            {answeredQuestions.map((question) => (
              <li key={question.id} className="rkm-item">
                <strong>{question.question}</strong>
                <p>{question.answer}</p>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </section>
  );
}
