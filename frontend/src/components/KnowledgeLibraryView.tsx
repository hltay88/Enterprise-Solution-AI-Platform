"use client";

import Link from "next/link";
import { useCallback, useEffect, useState, type FormEvent } from "react";

import { AppHeader } from "@/components/AppHeader";
import { apiFormPost, apiGet, ApiClientError } from "@/lib/api";
import type {
  KnowledgeItemDetail,
  KnowledgeItemSummary,
  KnowledgeType,
  TaxonomyDomain,
  UserPublic,
} from "@/lib/types";

type Props = { user: UserPublic };

type ListState =
  | { kind: "loading" }
  | { kind: "ready"; items: KnowledgeItemSummary[] }
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

export function KnowledgeLibraryView({ user }: Props) {
  const [state, setState] = useState<ListState>({ kind: "loading" });
  const [domains, setDomains] = useState<TaxonomyDomain[]>([]);
  const [types, setTypes] = useState<KnowledgeType[]>([]);
  const [statusFilter, setStatusFilter] = useState("");
  const [domainFilter, setDomainFilter] = useState("");
  const [q, setQ] = useState("");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [knowledgeType, setKnowledgeType] = useState("best_practice");
  const [domainCode, setDomainCode] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [contentText, setContentText] = useState("");
  const [busy, setBusy] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [createdId, setCreatedId] = useState<string | null>(null);

  const load = useCallback(async () => {
    setState({ kind: "loading" });
    try {
      const params = new URLSearchParams();
      if (statusFilter) params.set("status", statusFilter);
      if (domainFilter) params.set("domain_code", domainFilter);
      if (q.trim()) params.set("q", q.trim());
      const qs = params.toString();
      const items = await apiGet<KnowledgeItemSummary[]>(
        `/api/v1/knowledge${qs ? `?${qs}` : ""}`,
        true,
      );
      setState({ kind: "ready", items });
    } catch (error) {
      setState({
        kind: "error",
        message:
          error instanceof ApiClientError ? error.message : "Unable to load knowledge",
      });
    }
  }, [statusFilter, domainFilter, q]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    let cancelled = false;
    async function loadMeta() {
      try {
        const [d, t] = await Promise.all([
          apiGet<TaxonomyDomain[]>("/api/v1/knowledge/taxonomy/domains", true),
          apiGet<KnowledgeType[]>("/api/v1/knowledge/taxonomy/types", true),
        ]);
        if (!cancelled) {
          setDomains(d);
          setTypes(t);
        }
      } catch {
        /* taxonomy optional for list view */
      }
    }
    void loadMeta();
    return () => {
      cancelled = true;
    };
  }, []);

  async function onCreate(event: FormEvent) {
    event.preventDefault();
    setFormError(null);
    setCreatedId(null);
    if (!title.trim()) {
      setFormError("Title is required");
      return;
    }
    setBusy(true);
    try {
      const fields: Record<string, string> = {
        title: title.trim(),
        knowledge_type: knowledgeType,
        sensitivity: "internal",
      };
      if (description.trim()) fields.description = description.trim();
      if (domainCode) fields.domain_code = domainCode;
      if (contentText.trim()) fields.content_text = contentText.trim();
      const created = await apiFormPost<KnowledgeItemDetail>(
        "/api/v1/knowledge",
        fields,
        file,
      );
      setCreatedId(created.id);
      setTitle("");
      setDescription("");
      setContentText("");
      setFile(null);
      setDomainCode("");
      await load();
    } catch (error) {
      setFormError(
        error instanceof ApiClientError ? error.message : "Create failed",
      );
    } finally {
      setBusy(false);
    }
  }

  const isApprover = (user.role || "").toLowerCase() === "approver";

  return (
    <div className="shell">
      <AppHeader userName={user.name} showDashboardLink showKnowledgeLink />
      <main className="page">
        <section className="page-header">
          <h1>Enterprise Knowledge Library</h1>
          <p>
            Governed knowledge items with versioning and lifecycle — distinct from
            project Requirement Knowledge Models (RKM).
            {isApprover ? " You can approve and publish." : " Editors create drafts; Approvers publish."}
          </p>
        </section>

        <section className="panel">
          <div className="panel-heading">
            <h2>Create knowledge</h2>
          </div>
          <form className="stack-form" onSubmit={onCreate}>
            <label>
              Title
              <input value={title} onChange={(e) => setTitle(e.target.value)} required />
            </label>
            <label>
              Description
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={2}
              />
            </label>
            <div className="form-row">
              <label>
                Type
                <select
                  value={knowledgeType}
                  onChange={(e) => setKnowledgeType(e.target.value)}
                >
                  {types.map((t) => (
                    <option key={t.code} value={t.code}>
                      {t.name}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Domain (optional — auto-classified if empty)
                <select
                  value={domainCode}
                  onChange={(e) => setDomainCode(e.target.value)}
                >
                  <option value="">Auto-detect</option>
                  {domains.map((d) => (
                    <option key={d.code} value={d.code}>
                      {d.name}
                    </option>
                  ))}
                </select>
              </label>
            </div>
            <label>
              Content (optional if uploading a file)
              <textarea
                value={contentText}
                onChange={(e) => setContentText(e.target.value)}
                rows={4}
                placeholder="Paste markdown or text…"
              />
            </label>
            <label>
              Source file (PDF, DOCX, PPTX, XLSX, MD, TXT)
              <input
                type="file"
                accept=".pdf,.docx,.pptx,.xlsx,.md,.markdown,.txt"
                onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              />
            </label>
            {formError ? <p className="status status-error">{formError}</p> : null}
            {createdId ? (
              <p className="status">
                Created.{" "}
                <Link className="table-link" href={`/knowledge/${createdId}`}>
                  Open item
                </Link>
              </p>
            ) : null}
            <button className="btn-primary" type="submit" disabled={busy}>
              {busy ? "Saving…" : "Create draft"}
            </button>
          </form>
        </section>

        <section className="panel">
          <div className="panel-heading">
            <h2>Library</h2>
            <button className="btn-secondary btn-compact" type="button" onClick={() => void load()}>
              Refresh
            </button>
          </div>
          <div className="form-row filters">
            <label>
              Status
              <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
                <option value="">All</option>
                <option value="draft">Draft</option>
                <option value="review">Review</option>
                <option value="approved">Approved</option>
                <option value="published">Published</option>
                <option value="deprecated">Deprecated</option>
                <option value="archived">Archived</option>
              </select>
            </label>
            <label>
              Domain
              <select value={domainFilter} onChange={(e) => setDomainFilter(e.target.value)}>
                <option value="">All</option>
                {domains.map((d) => (
                  <option key={d.code} value={d.code}>
                    {d.name}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Search
              <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Title or content" />
            </label>
          </div>

          {state.kind === "loading" ? <p className="status">Loading…</p> : null}
          {state.kind === "error" ? (
            <p className="status status-error">{state.message}</p>
          ) : null}
          {state.kind === "ready" && state.items.length === 0 ? (
            <div className="empty-state">
              <p>No knowledge items yet.</p>
            </div>
          ) : null}
          {state.kind === "ready" && state.items.length > 0 ? (
            <div className="table-wrap">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Title</th>
                    <th>Domain</th>
                    <th>Type</th>
                    <th>Status</th>
                    <th>Version</th>
                    <th>Updated</th>
                  </tr>
                </thead>
                <tbody>
                  {state.items.map((item) => (
                    <tr key={item.id}>
                      <td>
                        <Link className="table-link" href={`/knowledge/${item.id}`}>
                          {item.title}
                        </Link>
                      </td>
                      <td>{item.domain_code}</td>
                      <td>{item.knowledge_type}</td>
                      <td>
                        <span className="status-pill">{item.status || "—"}</span>
                      </td>
                      <td>v{item.version_label || "—"}</td>
                      <td>{formatDate(item.updated_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : null}
        </section>
      </main>
    </div>
  );
}
