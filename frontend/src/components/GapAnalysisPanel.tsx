"use client";

import { FormEvent, useEffect, useState } from "react";

import { apiGet, apiPost, ApiClientError } from "@/lib/api";
import type {
  ClarificationAnswerResult,
  GapAnalysisReport,
  RkmClarification,
  RkmDraft,
} from "@/lib/types";

type GapAnalysisPanelProps = {
  projectId: string;
  onDraftUpdated?: (versionLabel?: string) => void;
};

type PanelState =
  | { kind: "loading" }
  | { kind: "no_draft" }
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
  const [lastVersion, setLastVersion] = useState<string | null>(null);

  async function checkDraftExists(): Promise<boolean> {
    try {
      const draft = await apiGet<RkmDraft>(
        `/api/v1/projects/${projectId}/requirements?status=draft`,
        true,
      );
      setLastVersion(draft.version.number);
      return true;
    } catch (err) {
      if (err instanceof ApiClientError && err.status === 404) {
        return false;
      }
      throw err;
    }
  }

  async function loadClarifications() {
    try {
      const hasDraft = await checkDraftExists();
      if (!hasDraft) {
        setQuestions([]);
        setState({ kind: "no_draft" });
        return;
      }

      const items = await apiGet<RkmClarification[]>(
        `/api/v1/projects/${projectId}/clarification`,
        true,
      );
      setQuestions(items);
      setState((prev) => (prev.kind === "ready" ? prev : { kind: "idle" }));
    } catch (err) {
      if (err instanceof ApiClientError && err.status === 404) {
        setQuestions([]);
        setState({ kind: "no_draft" });
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

  async function runGapAnalysis(options?: { preserveNote?: string }) {
    setRunning(true);
    setError(null);
    if (!options?.preserveNote) {
      setNote(null);
    }
    try {
      const hasDraft = await checkDraftExists();
      if (!hasDraft) {
        setState({ kind: "no_draft" });
        setQuestions([]);
        setError(null);
        setNote("Generate a Draft RKM above first, then run gap analysis here.");
        return;
      }

      const report = await apiPost<GapAnalysisReport>(
        `/api/v1/projects/${projectId}/requirements/gap-analysis`,
        {},
        true,
      );
      setState({ kind: "ready", report });
      setQuestions(report.clarifications);
      setLastVersion(report.version_label);
      const validIds = new Set(report.clarifications.map((item) => item.id));
      setAnswers((prev) =>
        Object.fromEntries(
          Object.entries(prev).filter(([id]) => validIds.has(id)),
        ),
      );
      setNote(
        options?.preserveNote
          || `Gap analysis complete · Draft RKM v${report.version_label} · overall ${Math.round(report.overall_quality)}% (${report.quality_level.replaceAll("_", " ")})`,
      );
      // Do not remount Draft RKM panel here — that steals focus to "Regenerate Draft RKM".
    } catch (err) {
      const message =
        err instanceof ApiClientError
          ? err.message
          : "Gap analysis failed — generate a Draft RKM first";
      if (
        err instanceof ApiClientError &&
        (err.status === 404 || message.toLowerCase().includes("no draft rkm"))
      ) {
        setState({ kind: "no_draft" });
        setQuestions([]);
        setError(null);
        setNote("Generate a Draft RKM above first, then run gap analysis here.");
      } else {
        setError(message);
      }
    } finally {
      setRunning(false);
    }
  }

  async function submitAnswers(event: FormEvent) {
    event.preventDefault();
    const validIds = new Set(questions.map((item) => item.id));
    const payload = Object.entries(answers)
      .map(([clarification_id, answer]) => ({
        clarification_id,
        answer: answer.trim(),
      }))
      .filter(
        (item) => item.answer.length > 0 && validIds.has(item.clarification_id),
      );

    if (payload.length === 0) {
      setError(
        "Enter at least one clarification answer for the current open questions.",
      );
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
      setLastVersion(result.version_label);
      const successNote =
        `Saved ${result.answered_count} answer(s). Draft RKM updated to v${result.version_label} — check the Draft RKM panel above for the new version.`;
      setNote(successNote);
      onDraftUpdated?.(result.version_label);
      // Soft refresh scores; keep the version-update message visible.
      await runGapAnalysis({ preserveNote: successNote });
      document
        .getElementById("draft-rkm-panel")
        ?.scrollIntoView({ behavior: "smooth", block: "start" });
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
  const canRun = state.kind !== "no_draft" && state.kind !== "loading";

  return (
    <section className="panel gap-panel" id="gap-analysis-panel">
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
          disabled={running || saving || !canRun}
        >
          {running ? "Analyzing…" : "Run gap analysis"}
        </button>
      </div>

      {error ? <p className="form-error">{error}</p> : null}
      {note ? <p className="status">{note}</p> : null}
      {lastVersion && state.kind !== "no_draft" ? (
        <p className="muted">Active Draft RKM version: v{lastVersion}</p>
      ) : null}

      {state.kind === "no_draft" ? (
        <div className="empty-state">
          <p>No Draft RKM yet — gap analysis needs a draft first.</p>
          <p className="muted">
            Scroll up to <strong>Draft Requirement Knowledge Model</strong>,
            click <strong>Generate Draft RKM</strong>, wait until it is ready,
            then return here and run gap analysis to get answer boxes.
          </p>
        </div>
      ) : null}

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
            Click <strong>Run gap analysis</strong> to score the Draft RKM and
            generate clarification answer boxes.
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
