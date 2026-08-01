"use client";

import { FormEvent, useEffect, useState } from "react";

import { apiGet, apiUpload, ApiClientError } from "@/lib/api";
import type { DocumentSummary } from "@/lib/types";

type DocumentUploadPanelProps = {
  projectId: string;
};

type ListState =
  | { kind: "loading" }
  | { kind: "ready"; documents: DocumentSummary[] }
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

export function DocumentUploadPanel({ projectId }: DocumentUploadPanelProps) {
  const [state, setState] = useState<ListState>({ kind: "loading" });
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  async function loadDocuments() {
    try {
      const documents = await apiGet<DocumentSummary[]>(
        `/api/projects/${projectId}/documents`,
        true,
      );
      setState({ kind: "ready", documents });
    } catch (error) {
      setState({
        kind: "error",
        message:
          error instanceof ApiClientError
            ? error.message
            : "Unable to load documents",
      });
    }
  }

  useEffect(() => {
    void loadDocuments();
  }, [projectId]);

  async function handleUpload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!file) {
      setUploadError("Choose a PDF, DOCX, or TXT file first");
      return;
    }

    setUploading(true);
    setUploadError(null);
    try {
      await apiUpload<DocumentSummary>(`/api/projects/${projectId}/upload`, file, true);
      setFile(null);
      await loadDocuments();
    } catch (error) {
      setUploadError(
        error instanceof ApiClientError ? error.message : "Upload failed",
      );
    } finally {
      setUploading(false);
    }
  }

  return (
    <section className="panel upload-panel">
      <div className="panel-heading">
        <h2>Requirement documents</h2>
        <p className="muted">PDF, DOCX, or TXT · max 10 MB · text is extracted on upload</p>
      </div>

      <form className="upload-form" onSubmit={handleUpload}>
        <input
          type="file"
          accept=".pdf,.docx,.txt,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,text/plain"
          onChange={(event) => setFile(event.target.files?.[0] ?? null)}
        />
        <button className="btn-primary btn-compact" type="submit" disabled={uploading}>
          {uploading ? "Uploading…" : "Upload & extract"}
        </button>
      </form>
      {uploadError ? <p className="form-error">{uploadError}</p> : null}

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
            return (
              <li key={document.id} className="doc-item">
                <div className="doc-meta">
                  <strong>{document.filename}</strong>
                  <span className="muted">
                    {document.file_type.toUpperCase()} · {formatDate(document.uploaded_at)}
                  </span>
                </div>
                <p className="doc-preview">
                  {document.extracted_preview || "No extracted text preview"}
                </p>
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
