"use client";

import { useEffect, useState } from "react";

import { apiGet, apiPatch, apiPost, ApiClientError } from "@/lib/api";
import type {
  ArchitectureOptionSummary,
  DeliverableSection,
  DeliverableValidation,
  ExportJob,
  GeneratedDocument,
} from "@/lib/types";

type DeliverablesPanelProps = {
  projectId: string;
  refreshToken?: number;
};

export function DeliverablesPanel({
  projectId,
  refreshToken = 0,
}: DeliverablesPanelProps) {
  const [docs, setDocs] = useState<GeneratedDocument[]>([]);
  const [completeArch, setCompleteArch] = useState<ArchitectureOptionSummary[]>(
    [],
  );
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [sections, setSections] = useState<DeliverableSection[]>([]);
  const [validation, setValidation] = useState<DeliverableValidation | null>(
    null,
  );
  const [exportJob, setExportJob] = useState<ExportJob | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [note, setNote] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const [rows, options] = await Promise.all([
        apiGet<GeneratedDocument[]>(
          `/api/v1/projects/${projectId}/deliverables`,
          true,
        ),
        apiGet<ArchitectureOptionSummary[]>(
          `/api/v1/projects/${projectId}/architectures`,
          true,
        ).catch(() => [] as ArchitectureOptionSummary[]),
      ]);
      setDocs(rows);
      setCompleteArch(
        options.filter((row) => (row.status || "").toLowerCase() === "complete"),
      );
      if (rows.length && !selectedId) {
        setSelectedId(rows[0].id);
      }
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : "Failed to load");
    } finally {
      setLoading(false);
    }
  }

  async function loadSections(documentId: string) {
    const rows = await apiGet<DeliverableSection[]>(
      `/api/v1/projects/${projectId}/deliverables/${documentId}/sections`,
      true,
    );
    setSections(rows);
  }

  useEffect(() => {
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId, refreshToken]);

  useEffect(() => {
    if (!selectedId) {
      setSections([]);
      return;
    }
    void loadSections(selectedId).catch((err) => {
      setError(err instanceof ApiClientError ? err.message : "Failed sections");
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedId]);

  const selected = docs.find((d) => d.id === selectedId) || null;

  async function run(action: string, fn: () => Promise<void>) {
    setBusy(action);
    setError(null);
    setNote(null);
    try {
      await fn();
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : String(err));
    } finally {
      setBusy(null);
    }
  }

  return (
    <section className="form-panel">
      <h2>Deliverables — Proposal</h2>
      <p className="muted">
        Generate a customer proposal from a Complete architecture via an
        immutable source snapshot (Sprint 4.1 / ATLAS-042…048).
      </p>

      {loading ? <p>Loading…</p> : null}
      {error ? <p className="error-text">{error}</p> : null}
      {note ? <p className="muted">{note}</p> : null}

      <div className="button-row" style={{ gap: 8, flexWrap: "wrap" }}>
        <button
          type="button"
          className="btn-primary"
          disabled={!!busy || completeArch.length === 0}
          onClick={() =>
            void run("generate", async () => {
              const doc = await apiPost<GeneratedDocument>(
                `/api/v1/projects/${projectId}/deliverables/generate`,
                { document_type: "proposal" },
                true,
              );
              setNote(`Generated draft: ${doc.title}`);
              setSelectedId(doc.id);
              await load();
              await loadSections(doc.id);
            })
          }
        >
          {busy === "generate" ? "Generating…" : "Generate proposal"}
        </button>
        <button
          type="button"
          className="btn-secondary"
          disabled={!!busy || !selectedId}
          onClick={() =>
            void run("validate", async () => {
              const result = await apiPost<DeliverableValidation>(
                `/api/v1/projects/${projectId}/deliverables/${selectedId}/validate`,
                {},
                true,
              );
              setValidation(result);
              setNote(result.ok ? "Validation passed" : "Validation has issues");
            })
          }
        >
          Validate
        </button>
        <button
          type="button"
          className="btn-secondary"
          disabled={!!busy || !selectedId}
          onClick={() =>
            void run("review", async () => {
              const doc = await apiPost<GeneratedDocument>(
                `/api/v1/projects/${projectId}/deliverables/${selectedId}/review`,
                {},
                true,
              );
              setNote(`Status: ${doc.status}`);
              await load();
            })
          }
        >
          Mark in review
        </button>
        <button
          type="button"
          className="btn-secondary"
          disabled={!!busy || !selectedId}
          onClick={() =>
            void run("approve", async () => {
              const doc = await apiPost<GeneratedDocument>(
                `/api/v1/projects/${projectId}/deliverables/${selectedId}/approve`,
                { decision: "approved" },
                true,
              );
              setNote(`Approved: ${doc.title}`);
              await load();
            })
          }
        >
          Approve
        </button>
        <button
          type="button"
          className="btn-secondary"
          disabled={!!busy || !selectedId}
          onClick={() =>
            void run("export", async () => {
              const job = await apiPost<ExportJob>(
                `/api/v1/projects/${projectId}/deliverables/${selectedId}/export`,
                { format: "docx" },
                true,
              );
              setExportJob(job);
              setNote(
                job.status === "completed"
                  ? `DOCX ready (checksum ${job.checksum_sha256?.slice(0, 12)}…)`
                  : `Export ${job.status}`,
              );
            })
          }
        >
          Export DOCX
        </button>
      </div>

      {completeArch.length === 0 ? (
        <p className="muted">
          No Complete architecture yet. Finish Architecture → Approve Complete
          before generating a proposal.
        </p>
      ) : null}

      {docs.length > 0 ? (
        <div style={{ marginTop: 12 }}>
          <label>
            Deliverable{" "}
            <select
              value={selectedId || ""}
              onChange={(e) => setSelectedId(e.target.value || null)}
            >
              {docs.map((doc) => (
                <option key={doc.id} value={doc.id}>
                  {doc.title} — {doc.status}
                  {doc.version_label ? ` v${doc.version_label}` : ""}
                </option>
              ))}
            </select>
          </label>
        </div>
      ) : null}

      {selected ? (
        <p className="muted" style={{ marginTop: 8 }}>
          Status <strong>{selected.status}</strong>
          {selected.bom_validated === false
            ? " · BOM not validated (pricing excluded)"
            : null}
          {exportJob?.checksum_sha256
            ? ` · Last export ${exportJob.status}`
            : null}
        </p>
      ) : null}

      {validation ? (
        <div style={{ marginTop: 8 }}>
          <h3>Validation</h3>
          <p>{validation.ok ? "OK" : "Issues found"}</p>
          <ul>
            {validation.issues.map((issue, index) => (
              <li key={`${issue.code}-${index}`}>
                [{issue.severity}] {issue.message}
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {sections.length > 0 ? (
        <div style={{ marginTop: 12 }}>
          <h3>Sections</h3>
          {sections.map((section) => (
            <details key={section.id} style={{ marginBottom: 8 }}>
              <summary>
                {section.title}{" "}
                {section.content_items.some((i) => i.review_required)
                  ? "· REVIEW REQUIRED"
                  : ""}
              </summary>
              {section.content_items.map((item) => (
                <div key={item.id} style={{ marginLeft: 12, marginTop: 6 }}>
                  <p>
                    {item.review_required ? (
                      <strong>[REVIEW REQUIRED] </strong>
                    ) : null}
                    {item.text}
                  </p>
                  {selected &&
                  (selected.status === "draft" ||
                    selected.status === "changes_requested") ? (
                    <button
                      type="button"
                      className="btn-secondary"
                      disabled={!!busy}
                      onClick={() =>
                        void run("patch", async () => {
                          const next = window.prompt(
                            "Edit section text",
                            item.text,
                          );
                          if (next == null) return;
                          await apiPatch<DeliverableSection>(
                            `/api/v1/projects/${projectId}/deliverables/${selected.id}/sections/${section.id}`,
                            { text: next },
                            true,
                          );
                          await loadSections(selected.id);
                        })
                      }
                    >
                      Edit text
                    </button>
                  ) : null}
                </div>
              ))}
            </details>
          ))}
        </div>
      ) : null}
    </section>
  );
}
