"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { AppHeader } from "@/components/AppHeader";
import { apiGet, apiPatch, apiPost, apiUpload, ApiClientError } from "@/lib/api";
import type { KnowledgeItemDetail, UserPublic } from "@/lib/types";

type Props = {
  user: UserPublic;
  knowledgeId: string;
};

function formatDate(value: string | null | undefined): string {
  if (!value) return "—";
  try {
    return new Intl.DateTimeFormat(undefined, {
      dateStyle: "medium",
      timeStyle: "short",
    }).format(new Date(value));
  } catch {
    return value;
  }
}

export function KnowledgeDetailView({ user, knowledgeId }: Props) {
  const [item, setItem] = useState<KnowledgeItemDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [editContent, setEditContent] = useState("");
  const [message, setMessage] = useState<string | null>(null);

  const isApprover = (user.role || "").toLowerCase() === "approver";
  const status = item?.current_version?.status || item?.status || "";

  const load = useCallback(async () => {
    setError(null);
    try {
      const data = await apiGet<KnowledgeItemDetail>(`/api/v1/knowledge/${knowledgeId}`, true);
      setItem(data);
      setEditContent(data.current_version?.content_text || "");
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : "Failed to load");
    }
  }, [knowledgeId]);

  useEffect(() => {
    void load();
  }, [load]);

  async function runAction(path: string, okMessage: string) {
    setBusy(true);
    setMessage(null);
    setError(null);
    try {
      const data = await apiPost<KnowledgeItemDetail>(path, {}, true);
      setItem(data);
      setEditContent(data.current_version?.content_text || "");
      setMessage(okMessage);
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : "Action failed");
    } finally {
      setBusy(false);
    }
  }

  async function saveDraft() {
    setBusy(true);
    setMessage(null);
    setError(null);
    try {
      const data = await apiPatch<KnowledgeItemDetail>(
        `/api/v1/knowledge/${knowledgeId}`,
        { content_text: editContent },
        true,
      );
      setItem(data);
      setMessage("Draft saved");
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : "Save failed");
    } finally {
      setBusy(false);
    }
  }

  async function onIngest(file: File | null) {
    if (!file) return;
    setBusy(true);
    setMessage(null);
    setError(null);
    try {
      const data = await apiUpload<KnowledgeItemDetail>(
        `/api/v1/knowledge/${knowledgeId}/ingest`,
        file,
        true,
      );
      setItem(data);
      setEditContent(data.current_version?.content_text || "");
      setMessage(`Ingested ${file.name}`);
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : "Ingest failed");
    } finally {
      setBusy(false);
    }
  }

  if (error && !item) {
    return (
      <div className="shell">
        <AppHeader userName={user.name} showDashboardLink showKnowledgeLink />
        <main className="page">
          <p className="status status-error">{error}</p>
          <Link href="/knowledge">Back to library</Link>
        </main>
      </div>
    );
  }

  if (!item) {
    return (
      <div className="shell">
        <AppHeader userName={user.name} showDashboardLink showKnowledgeLink />
        <main className="page">
          <p className="status">Loading…</p>
        </main>
      </div>
    );
  }

  const version = item.current_version;

  return (
    <div className="shell">
      <AppHeader userName={user.name} showDashboardLink showKnowledgeLink />
      <main className="page">
        <section className="page-header">
          <p className="muted">
            <Link className="table-link" href="/knowledge">
              ← Knowledge Library
            </Link>
          </p>
          <h1>{item.title}</h1>
          <p>
            {item.description || "No description."} · Domain{" "}
            <strong>{item.domain_code}</strong> · Type{" "}
            <strong>{item.knowledge_type}</strong> ·{" "}
            <span className="status-pill">{status}</span> · v{item.version_label}
          </p>
        </section>

        {message ? <p className="status">{message}</p> : null}
        {error ? <p className="status status-error">{error}</p> : null}

        <section className="panel">
          <div className="panel-heading">
            <h2>Lifecycle</h2>
          </div>
          <div className="button-row">
            {status === "draft" ? (
              <>
                <button
                  className="btn-primary btn-compact"
                  type="button"
                  disabled={busy}
                  onClick={() =>
                    void runAction(
                      `/api/v1/knowledge/${knowledgeId}/submit-review`,
                      "Submitted for review",
                    )
                  }
                >
                  Submit for review
                </button>
                <button
                  className="btn-secondary btn-compact"
                  type="button"
                  disabled={busy}
                  onClick={() => void saveDraft()}
                >
                  Save draft content
                </button>
              </>
            ) : null}
            {status === "review" ? (
              <>
                <button
                  className="btn-secondary btn-compact"
                  type="button"
                  disabled={busy}
                  onClick={() =>
                    void runAction(
                      `/api/v1/knowledge/${knowledgeId}/return-draft`,
                      "Returned to draft",
                    )
                  }
                >
                  Return to draft
                </button>
                {isApprover ? (
                  <button
                    className="btn-primary btn-compact"
                    type="button"
                    disabled={busy}
                    onClick={() =>
                      void runAction(
                        `/api/v1/knowledge/${knowledgeId}/approve`,
                        "Approved",
                      )
                    }
                  >
                    Approve
                  </button>
                ) : null}
              </>
            ) : null}
            {status === "approved" && isApprover ? (
              <button
                className="btn-primary btn-compact"
                type="button"
                disabled={busy}
                onClick={() =>
                  void runAction(
                    `/api/v1/knowledge/${knowledgeId}/publish`,
                    "Published (immutable)",
                  )
                }
              >
                Publish
              </button>
            ) : null}
            {status === "published" && isApprover ? (
              <button
                className="btn-secondary btn-compact"
                type="button"
                disabled={busy}
                onClick={() =>
                  void runAction(
                    `/api/v1/knowledge/${knowledgeId}/deprecate`,
                    "Deprecated",
                  )
                }
              >
                Deprecate
              </button>
            ) : null}
            {status === "deprecated" && isApprover ? (
              <button
                className="btn-secondary btn-compact"
                type="button"
                disabled={busy}
                onClick={() =>
                  void runAction(
                    `/api/v1/knowledge/${knowledgeId}/archive`,
                    "Archived",
                  )
                }
              >
                Archive
              </button>
            ) : null}
            {status === "published" || status === "deprecated" || status === "approved" ? (
              <button
                className="btn-primary btn-compact"
                type="button"
                disabled={busy}
                onClick={() =>
                  void runAction(
                    `/api/v1/knowledge/${knowledgeId}/new-version`,
                    "New draft version created",
                  )
                }
              >
                New version
              </button>
            ) : null}
          </div>
          <p className="muted" style={{ marginTop: "0.75rem" }}>
            Published versions are immutable. Changes require a new version.
          </p>
        </section>

        {status === "draft" ? (
          <section className="panel">
            <div className="panel-heading">
              <h2>Ingest source file</h2>
            </div>
            <input
              type="file"
              accept=".pdf,.docx,.pptx,.xlsx,.md,.markdown,.txt"
              disabled={busy}
              onChange={(e) => void onIngest(e.target.files?.[0] ?? null)}
            />
          </section>
        ) : null}

        <section className="panel">
          <div className="panel-heading">
            <h2>Current content (v{version?.version_label})</h2>
          </div>
          {version?.source_document_name ? (
            <p className="muted">
              Source: {version.source_document_name}
              {version.sources?.[0]
                ? ` · ${version.sources[0].file_type.toUpperCase()} · ${version.sources[0].page_count ?? "?"} page(s)`
                : null}
            </p>
          ) : null}
          {status === "draft" ? (
            <textarea
              value={editContent}
              onChange={(e) => setEditContent(e.target.value)}
              rows={16}
              style={{ width: "100%", fontFamily: "ui-monospace, monospace" }}
            />
          ) : (
            <pre className="knowledge-content">{version?.content_text || "(empty)"}</pre>
          )}
        </section>

        <section className="panel">
          <div className="panel-heading">
            <h2>Version history</h2>
          </div>
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Version</th>
                  <th>Status</th>
                  <th>Summary</th>
                  <th>Published</th>
                  <th>Updated</th>
                </tr>
              </thead>
              <tbody>
                {(item.versions || []).slice().reverse().map((v) => (
                  <tr key={v.id}>
                    <td>v{v.version_label}</td>
                    <td>
                      <span className="status-pill">{v.status}</span>
                    </td>
                    <td>{v.change_summary || "—"}</td>
                    <td>{formatDate(v.published_at)}</td>
                    <td>{formatDate(v.updated_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      </main>
    </div>
  );
}
