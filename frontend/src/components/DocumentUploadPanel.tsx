"use client";

import { FormEvent, useEffect, useRef, useState } from "react";

import {
  apiDelete,
  apiGet,
  apiUploadMany,
  ApiClientError,
} from "@/lib/api";
import type {
  DocumentSummary,
  DocumentUploadBatchResult,
  JobStatus,
} from "@/lib/types";

type DocumentUploadPanelProps = {
  projectId: string;
};

type ListState =
  | { kind: "loading" }
  | { kind: "ready"; documents: DocumentSummary[] }
  | { kind: "error"; message: string };

const ACCEPT =
  ".pdf,.docx,.doc,.xlsx,.csv,.txt,.png,.jpg,.jpeg,application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,text/csv,text/plain,image/png,image/jpeg";

const MAX_FILE_MB = 50;
const MAX_BATCH_MB = 200;
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

function formatBytes(value: number | null | undefined): string {
  if (value == null) return "";
  if (value < 1024) return `${value} B`;
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`;
  return `${(value / (1024 * 1024)).toFixed(1)} MB`;
}

function statusLabel(document: DocumentSummary): string {
  const status = document.status || "completed";
  if (status === "pending" || status === "processing") {
    return status === "pending" ? "Queued" : "Extracting…";
  }
  if (status === "failed") return "Failed";
  if (document.needs_manual_review) return "Needs review";
  if (document.ocr_used) return "Ready (OCR)";
  return "Ready";
}

export function DocumentUploadPanel({ projectId }: DocumentUploadPanelProps) {
  const [state, setState] = useState<ListState>({ kind: "loading" });
  const [files, setFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadNote, setUploadNote] = useState<string | null>(null);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [removingId, setRemovingId] = useState<string | null>(null);
  const [removeError, setRemoveError] = useState<string | null>(null);
  const [jobProgress, setJobProgress] = useState<Record<string, number>>({});
  const pollTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  async function loadDocuments() {
    try {
      const documents = await apiGet<DocumentSummary[]>(
        `/api/v1/projects/${projectId}/documents`,
        true,
      );
      setState({ kind: "ready", documents });
      return documents;
    } catch (error) {
      setState({
        kind: "error",
        message:
          error instanceof ApiClientError
            ? error.message
            : "Unable to load documents",
      });
      return [];
    }
  }

  function clearPoll() {
    if (pollTimer.current) {
      clearTimeout(pollTimer.current);
      pollTimer.current = null;
    }
  }

  async function pollJobs(jobIds: string[]) {
    clearPoll();
    if (jobIds.length === 0) {
      await loadDocuments();
      return;
    }

    const remaining: string[] = [];
    const progress: Record<string, number> = {};

    for (const jobId of jobIds) {
      try {
        const job = await apiGet<JobStatus>(`/api/v1/jobs/${jobId}`, true);
        progress[jobId] = job.progress;
        if (job.status === "queued" || job.status === "processing") {
          remaining.push(jobId);
        }
      } catch {
        remaining.push(jobId);
      }
    }

    setJobProgress((prev) => ({ ...prev, ...progress }));
    await loadDocuments();

    if (remaining.length > 0) {
      pollTimer.current = setTimeout(() => {
        void pollJobs(remaining);
      }, POLL_MS);
    }
  }

  useEffect(() => {
    void loadDocuments().then((documents) => {
      const active = documents
        .filter((doc) => doc.status === "pending" || doc.status === "processing")
        .map((doc) => doc.processing_job_id)
        .filter((id): id is string => Boolean(id));
      if (active.length > 0) {
        void pollJobs(active);
      }
    });
    return () => clearPoll();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId]);

  async function handleUpload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (files.length === 0) {
      setUploadError("Choose one or more supported files first");
      return;
    }

    const batchBytes = files.reduce((sum, file) => sum + file.size, 0);
    if (batchBytes > MAX_BATCH_MB * 1024 * 1024) {
      setUploadError(`Batch exceeds ${MAX_BATCH_MB} MB aggregate limit`);
      return;
    }
    const oversized = files.find((file) => file.size > MAX_FILE_MB * 1024 * 1024);
    if (oversized) {
      setUploadError(`"${oversized.name}" exceeds ${MAX_FILE_MB} MB per-file limit`);
      return;
    }

    setUploading(true);
    setUploadError(null);
    setRemoveError(null);
    setUploadNote(null);
    try {
      const result = await apiUploadMany<DocumentUploadBatchResult>(
        "/api/v1/documents/upload",
        files,
        { project_id: projectId },
        true,
      );
      setFiles([]);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }

      const notes: string[] = [];
      if (result.accepted_count > 0) {
        notes.push(`${result.accepted_count} file(s) accepted for extraction`);
      }
      if (result.duplicate_count > 0) {
        notes.push(`${result.duplicate_count} duplicate(s) skipped (SHA-256)`);
      }
      setUploadNote(notes.join(" · ") || null);

      const jobIds = result.items
        .filter((item) => item.job?.id)
        .map((item) => item.job!.id);
      await loadDocuments();
      if (jobIds.length > 0) {
        void pollJobs(jobIds);
      }
    } catch (error) {
      setUploadError(
        error instanceof ApiClientError ? error.message : "Upload failed",
      );
    } finally {
      setUploading(false);
    }
  }

  async function handleRemove(document: DocumentSummary) {
    if (
      !window.confirm(
        `Archive "${document.filename}" from this project?`,
      )
    ) {
      return;
    }

    setRemovingId(document.id);
    setRemoveError(null);
    try {
      await apiDelete(`/api/v1/documents/${document.id}`, true);
      if (expandedId === document.id) {
        setExpandedId(null);
      }
      await loadDocuments();
    } catch (error) {
      setRemoveError(
        error instanceof ApiClientError ? error.message : "Unable to remove document",
      );
    } finally {
      setRemovingId(null);
    }
  }

  return (
    <section className="panel upload-panel">
      <div className="panel-heading">
        <h2>Requirement documents</h2>
        <p className="muted">
          PDF, DOCX, DOC, XLSX, CSV, TXT, PNG, JPG · {MAX_FILE_MB} MB/file ·{" "}
          {MAX_BATCH_MB} MB/batch · async extract + OCR
        </p>
      </div>

      <form className="upload-form" onSubmit={handleUpload}>
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept={ACCEPT}
          onChange={(event) =>
            setFiles(Array.from(event.target.files ?? []))
          }
        />
        <button className="btn-primary btn-compact" type="submit" disabled={uploading}>
          {uploading ? "Uploading…" : "Upload & extract"}
        </button>
      </form>
      {files.length > 0 ? (
        <p className="muted">
          {files.length} selected · {formatBytes(files.reduce((s, f) => s + f.size, 0))}
        </p>
      ) : null}
      {uploadError ? <p className="form-error">{uploadError}</p> : null}
      {uploadNote ? <p className="status">{uploadNote}</p> : null}
      {removeError ? <p className="form-error">{removeError}</p> : null}

      {state.kind === "loading" ? <p className="status">Loading documents…</p> : null}
      {state.kind === "error" ? (
        <p className="status status-error">{state.message}</p>
      ) : null}

      {state.kind === "ready" && state.documents.length === 0 ? (
        <div className="empty-state">
          <p>No documents uploaded yet.</p>
        </div>
      ) : null}

      {state.kind === "ready" && state.documents.length > 0 ? (
        <ul className="doc-list">
          {state.documents.map((document) => {
            const expanded = expandedId === document.id;
            const removing = removingId === document.id;
            const jobId = document.processing_job_id;
            const progress =
              jobId && jobProgress[jobId] != null ? jobProgress[jobId] : null;
            return (
              <li key={document.id} className="doc-item">
                <div className="doc-meta">
                  <strong>{document.filename}</strong>
                  <span className="muted">
                    {document.file_type.toUpperCase()}
                    {document.file_size_bytes != null
                      ? ` · ${formatBytes(document.file_size_bytes)}`
                      : ""}
                    {" · "}
                    {formatDate(document.uploaded_at)}
                    {" · "}
                    {statusLabel(document)}
                    {progress != null &&
                    (document.status === "pending" || document.status === "processing")
                      ? ` (${progress}%)`
                      : ""}
                  </span>
                </div>
                <p className="doc-preview">
                  {document.error_message
                    ? document.error_message
                    : document.extracted_preview ||
                      (document.status === "pending" || document.status === "processing"
                        ? "Extraction in progress…"
                        : "No extracted text preview")}
                </p>
                <div className="doc-actions">
                  {document.extracted_text ? (
                    <button
                      className="btn-secondary btn-compact"
                      type="button"
                      onClick={() =>
                        setExpandedId(expanded ? null : document.id)
                      }
                    >
                      {expanded ? "Hide full text" : "Show full text"}
                    </button>
                  ) : null}
                  <button
                    className="btn-secondary btn-compact"
                    type="button"
                    onClick={() => void handleRemove(document)}
                    disabled={removing}
                  >
                    {removing ? "Removing…" : "Remove"}
                  </button>
                </div>
                {expanded && document.extracted_text ? (
                  <pre className="doc-full-text">{document.extracted_text}</pre>
                ) : null}
              </li>
            );
          })}
        </ul>
      ) : null}
    </section>
  );
}
