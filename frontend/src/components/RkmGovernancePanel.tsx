"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";

import { apiGet, apiPost, ApiClientError } from "@/lib/api";
import type {
  ApproveResult,
  PublishResult,
  ReviewResult,
  RkmDraft,
  RkmRequirement,
  RkmVersionSummary,
  VersionCompare,
} from "@/lib/types";

type RkmGovernancePanelProps = {
  projectId: string;
  refreshToken?: number;
  onDraftUpdated?: (versionLabel?: string) => void;
};

type LoadState =
  | { kind: "loading" }
  | { kind: "empty" }
  | { kind: "ready"; draft: RkmDraft }
  | { kind: "error"; message: string };

const EDITABLE_SECTIONS: Array<{
  key: keyof RkmDraft;
  label: string;
}> = [
  { key: "business_objectives", label: "Business objectives" },
  { key: "functional_requirements", label: "Functional requirements" },
  { key: "non_functional_requirements", label: "Non-functional requirements" },
  { key: "constraints", label: "Constraints" },
  { key: "dependencies", label: "Dependencies" },
  { key: "risks", label: "Risks" },
  { key: "assumptions", label: "Assumptions" },
];

function collectRequirements(draft: RkmDraft): RkmRequirement[] {
  return EDITABLE_SECTIONS.flatMap(({ key }) => {
    const value = draft[key];
    return Array.isArray(value) ? (value as RkmRequirement[]) : [];
  });
}

export function RkmGovernancePanel({
  projectId,
  refreshToken = 0,
  onDraftUpdated,
}: RkmGovernancePanelProps) {
  const [state, setState] = useState<LoadState>({ kind: "loading" });
  const [published, setPublished] = useState<RkmDraft | null>(null);
  const [versions, setVersions] = useState<RkmVersionSummary[]>([]);
  const [selectedId, setSelectedId] = useState<string>("");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [priority, setPriority] = useState("medium");
  const [changeSummary, setChangeSummary] = useState("");
  const [reasoningNote, setReasoningNote] = useState("");
  const [approveNote, setApproveNote] = useState("");
  const [publishNote, setPublishNote] = useState("");
  const [fromVersion, setFromVersion] = useState("");
  const [toVersion, setToVersion] = useState("");
  const [compare, setCompare] = useState<VersionCompare | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [note, setNote] = useState<string | null>(null);

  async function loadAll() {
    setError(null);
    try {
      const draft = await apiGet<RkmDraft>(
        `/api/v1/projects/${projectId}/requirements?status=draft`,
        true,
      );
      setState({ kind: "ready", draft });
      const items = collectRequirements(draft);
      if (items.length && !selectedId) {
        setSelectedId(items[0].id);
        setTitle(items[0].title);
        setDescription(items[0].description);
        setPriority(items[0].priority || "medium");
      }
    } catch (err) {
      if (err instanceof ApiClientError && err.status === 404) {
        setState({ kind: "empty" });
      } else {
        setState({
          kind: "error",
          message:
            err instanceof ApiClientError
              ? err.message
              : "Unable to load Draft RKM",
        });
      }
    }

    try {
      const pub = await apiGet<RkmDraft>(
        `/api/v1/projects/${projectId}/requirements?status=published`,
        true,
      );
      setPublished(pub);
    } catch {
      setPublished(null);
    }

    try {
      const rows = await apiGet<RkmVersionSummary[]>(
        `/api/v1/projects/${projectId}/requirements/versions`,
        true,
      );
      setVersions(rows);
      if (rows.length >= 2) {
        setFromVersion((prev) => prev || rows[1].version_label);
        setToVersion((prev) => prev || rows[0].version_label);
      } else if (rows.length === 1) {
        setFromVersion(rows[0].version_label);
        setToVersion(rows[0].version_label);
      }
    } catch {
      setVersions([]);
    }
  }

  useEffect(() => {
    void loadAll();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId, refreshToken]);

  const requirements = useMemo(() => {
    if (state.kind !== "ready") return [];
    return collectRequirements(state.draft);
  }, [state]);

  useEffect(() => {
    const item = requirements.find((req) => req.id === selectedId);
    if (!item) return;
    setTitle(item.title);
    setDescription(item.description);
    setPriority(item.priority || "medium");
  }, [selectedId, requirements]);

  const approvalStatus =
    state.kind === "ready" ? state.draft.approval.status : null;
  const canEdit = state.kind === "ready" && approvalStatus !== "published";
  const canApprove =
    canEdit && approvalStatus !== "approved" && approvalStatus !== "published";
  const canPublish = canEdit && approvalStatus === "approved";

  async function saveReview(event: FormEvent) {
    event.preventDefault();
    if (!canEdit || !selectedId) return;
    setBusy("review");
    setError(null);
    setNote(null);
    try {
      const result = await apiPost<ReviewResult>(
        `/api/v1/projects/${projectId}/requirements/review`,
        {
          edits: [
            {
              id: selectedId,
              title: title.trim(),
              description: description.trim(),
              priority: priority.trim(),
            },
          ],
          change_summary: changeSummary.trim() || undefined,
          reasoning_note: reasoningNote.trim() || undefined,
        },
        true,
      );
      setNote(`Saved review as v${result.version_label}`);
      setChangeSummary("");
      setReasoningNote("");
      onDraftUpdated?.(result.version_label);
      await loadAll();
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : "Review failed");
    } finally {
      setBusy(null);
    }
  }

  async function approveDraft() {
    if (!canApprove) return;
    setBusy("approve");
    setError(null);
    setNote(null);
    try {
      const result = await apiPost<ApproveResult>(
        `/api/v1/projects/${projectId}/requirements/approve`,
        { note: approveNote.trim() || undefined },
        true,
      );
      setNote(`Approved v${result.version_label}`);
      setApproveNote("");
      onDraftUpdated?.(result.version_label);
      await loadAll();
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : "Approve failed");
    } finally {
      setBusy(null);
    }
  }

  async function publishDraft() {
    if (!canPublish) return;
    setBusy("publish");
    setError(null);
    setNote(null);
    try {
      const result = await apiPost<PublishResult>(
        `/api/v1/projects/${projectId}/requirements/publish`,
        { note: publishNote.trim() || undefined },
        true,
      );
      setNote(`Published v${result.version_label} for Phase 3`);
      setPublishNote("");
      onDraftUpdated?.(result.version_label);
      await loadAll();
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : "Publish failed");
    } finally {
      setBusy(null);
    }
  }

  async function forkDraft() {
    setBusy("fork");
    setError(null);
    setNote(null);
    try {
      const result = await apiPost<ReviewResult>(
        `/api/v1/projects/${projectId}/requirements/version`,
        {
          from_version: published?.version.number,
          change_summary: "Forked published RKM for continued review",
        },
        true,
      );
      setNote(`Forked new Draft v${result.version_label}`);
      onDraftUpdated?.(result.version_label);
      await loadAll();
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : "Fork failed");
    } finally {
      setBusy(null);
    }
  }

  async function runCompare() {
    if (!fromVersion || !toVersion) return;
    setBusy("compare");
    setError(null);
    try {
      const result = await apiGet<VersionCompare>(
        `/api/v1/projects/${projectId}/requirements/compare?from=${encodeURIComponent(fromVersion)}&to=${encodeURIComponent(toVersion)}`,
        true,
      );
      setCompare(result);
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : "Compare failed");
    } finally {
      setBusy(null);
    }
  }

  return (
    <section className="panel rkm-panel" id="rkm-governance-panel">
      <div className="panel-heading">
        <div>
          <h2>RKM governance</h2>
          <p className="muted">
            Edit Draft requirements, review AI reasoning, approve, and publish
            an immutable RKM (Stage E)
          </p>
        </div>
      </div>

      {state.kind === "loading" ? <p className="status">Loading…</p> : null}
      {state.kind === "empty" ? (
        <p className="muted">
          Generate a Draft RKM first, then return here to review and publish.
        </p>
      ) : null}
      {state.kind === "error" ? (
        <p className="status status-error">{state.message}</p>
      ) : null}
      {error ? <p className="form-error">{error}</p> : null}
      {note ? <p className="status">{note}</p> : null}

      {published ? (
        <div className="rkm-section">
          <h3>Published RKM</h3>
          <p className="muted">
            v{published.version.number} · immutable · Phase 3 input
            {published.approval.published_at
              ? ` · ${new Date(published.approval.published_at).toLocaleString()}`
              : ""}
          </p>
          {state.kind === "empty" ? (
            <button
              className="btn-secondary btn-compact"
              type="button"
              disabled={busy != null}
              onClick={() => void forkDraft()}
            >
              {busy === "fork" ? "Forking…" : "Fork new Draft from published"}
            </button>
          ) : null}
        </div>
      ) : null}

      {state.kind === "ready" ? (
        <>
          <div className="rkm-meta muted">
            <span>Draft v{state.draft.version.number}</span>
            <span> · {state.draft.approval.status.replaceAll("_", " ")}</span>
            {state.draft.approval.approved_by ? (
              <span> · Approved by {state.draft.approval.approved_by}</span>
            ) : null}
          </div>

          <details className="rkm-section" open>
            <summary>
              <strong>AI reasoning</strong>
            </summary>
            <p className="rkm-reasoning">
              {state.draft.analysis.reasoning_summary || "No reasoning summary."}
            </p>
          </details>

          {canEdit ? (
            <form className="rkm-section" onSubmit={saveReview}>
              <h3>Edit requirement</h3>
              <label className="field">
                <span>Requirement</span>
                <select
                  value={selectedId}
                  onChange={(event) => setSelectedId(event.target.value)}
                >
                  {requirements.map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.title}
                    </option>
                  ))}
                </select>
              </label>
              <label className="field">
                <span>Title</span>
                <input
                  value={title}
                  onChange={(event) => setTitle(event.target.value)}
                  required
                />
              </label>
              <label className="field">
                <span>Description</span>
                <textarea
                  className="gap-answer"
                  rows={4}
                  value={description}
                  onChange={(event) => setDescription(event.target.value)}
                  required
                />
              </label>
              <label className="field">
                <span>Priority</span>
                <select
                  value={priority}
                  onChange={(event) => setPriority(event.target.value)}
                >
                  <option value="critical">critical</option>
                  <option value="high">high</option>
                  <option value="medium">medium</option>
                  <option value="low">low</option>
                </select>
              </label>
              <label className="field">
                <span>Change summary</span>
                <input
                  value={changeSummary}
                  onChange={(event) => setChangeSummary(event.target.value)}
                  placeholder="Why this edit?"
                />
              </label>
              <label className="field">
                <span>Reviewer note (appended to reasoning)</span>
                <input
                  value={reasoningNote}
                  onChange={(event) => setReasoningNote(event.target.value)}
                />
              </label>
              <button
                className="btn-primary btn-compact"
                type="submit"
                disabled={busy != null || !requirements.length}
              >
                {busy === "review" ? "Saving…" : "Save edit (new patch version)"}
              </button>
            </form>
          ) : null}

          <div className="rkm-section governance-actions">
            <h3>Approval & publish</h3>
            {canApprove ? (
              <>
                <label className="field">
                  <span>Approval note</span>
                  <input
                    value={approveNote}
                    onChange={(event) => setApproveNote(event.target.value)}
                  />
                </label>
                <button
                  className="btn-primary btn-compact"
                  type="button"
                  disabled={busy != null}
                  onClick={() => void approveDraft()}
                >
                  {busy === "approve" ? "Approving…" : "Approve Draft RKM"}
                </button>
              </>
            ) : null}
            {canPublish ? (
              <>
                <label className="field">
                  <span>Publish note</span>
                  <input
                    value={publishNote}
                    onChange={(event) => setPublishNote(event.target.value)}
                  />
                </label>
                <button
                  className="btn-primary btn-compact"
                  type="button"
                  disabled={busy != null}
                  onClick={() => void publishDraft()}
                >
                  {busy === "publish" ? "Publishing…" : "Publish RKM"}
                </button>
                <p className="muted">
                  Publish enforces ≥85% completeness/confidence, no critical
                  gaps, and human approval.
                </p>
              </>
            ) : null}
            {!canApprove && !canPublish ? (
              <p className="muted">
                {approvalStatus === "approved"
                  ? "Draft is approved. Resolve any remaining publish blockers in Gap Analysis, then publish."
                  : approvalStatus === "published"
                    ? "This version is published and immutable."
                    : "Approve when the Draft is ready for the publish gate."}
              </p>
            ) : null}
          </div>
        </>
      ) : null}

      {versions.length > 0 ? (
        <div className="rkm-section">
          <h3>Version compare</h3>
          <div className="governance-compare-row">
            <label className="field">
              <span>From</span>
              <select
                value={fromVersion}
                onChange={(event) => setFromVersion(event.target.value)}
              >
                {versions.map((version) => (
                  <option key={version.id} value={version.version_label}>
                    v{version.version_label} ({version.status})
                  </option>
                ))}
              </select>
            </label>
            <label className="field">
              <span>To</span>
              <select
                value={toVersion}
                onChange={(event) => setToVersion(event.target.value)}
              >
                {versions.map((version) => (
                  <option key={version.id} value={version.version_label}>
                    v{version.version_label} ({version.status})
                  </option>
                ))}
              </select>
            </label>
            <button
              className="btn-secondary btn-compact"
              type="button"
              disabled={busy != null || !fromVersion || !toVersion}
              onClick={() => void runCompare()}
            >
              {busy === "compare" ? "Comparing…" : "Compare"}
            </button>
          </div>
          {compare ? (
            <div className="governance-compare-result">
              <p className="muted">
                {compare.summary.added ?? 0} added · {compare.summary.removed ?? 0}{" "}
                removed · {compare.summary.modified ?? 0} modified
                {compare.summary.reasoning_changed ? " · reasoning changed" : ""}
              </p>
              {compare.diffs.length === 0 ? (
                <p className="muted">No requirement text differences.</p>
              ) : (
                <ul className="rkm-list">
                  {compare.diffs.map((diff, index) => (
                    <li key={`${diff.section}-${diff.item_id}-${index}`} className="rkm-item">
                      <div className="rkm-item-head">
                        <strong>
                          {diff.change_type} · {diff.section.replaceAll("_", " ")}
                        </strong>
                        <span className="muted">{diff.title}</span>
                      </div>
                      {diff.before ? (
                        <p className="muted">Before: {diff.before}</p>
                      ) : null}
                      {diff.after ? <p>After: {diff.after}</p> : null}
                    </li>
                  ))}
                </ul>
              )}
              {compare.from_reasoning || compare.to_reasoning ? (
                <details>
                  <summary>Reasoning diff</summary>
                  <p className="muted">From: {compare.from_reasoning || "—"}</p>
                  <p>To: {compare.to_reasoning || "—"}</p>
                </details>
              ) : null}
            </div>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}
