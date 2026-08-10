"use client";

import Link from "next/link";
import { useEffect, useState, type FormEvent } from "react";

import { AppHeader } from "@/components/AppHeader";
import { apiGet, apiPost, ApiClientError } from "@/lib/api";
import type {
  RetrievalSearchResult,
  TaxonomyDomain,
  UserPublic,
} from "@/lib/types";

type Props = { user: UserPublic };

export function RetrievalExplorerView({ user }: Props) {
  const [query, setQuery] = useState("");
  const [domainCode, setDomainCode] = useState("");
  const [domains, setDomains] = useState<TaxonomyDomain[]>([]);
  const [result, setResult] = useState<RetrievalSearchResult | null>(null);
  const [mode, setMode] = useState<"search" | "context">("search");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    void apiGet<TaxonomyDomain[]>("/api/v1/knowledge/taxonomy/domains", true)
      .then((rows) => {
        if (!cancelled) setDomains(rows);
      })
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, []);

  async function onSearch(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    setResult(null);
    try {
      const body: Record<string, unknown> = { query: query.trim(), top_k: 8 };
      if (domainCode) body.domain_code = domainCode;
      const path =
        mode === "context"
          ? "/api/v1/retrieval/context"
          : "/api/v1/retrieval/search";
      const data = await apiPost<RetrievalSearchResult>(path, body, true);
      setResult(data);
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : "Retrieval failed");
    } finally {
      setBusy(false);
    }
  }

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
          <h1>Retrieval Explorer</h1>
          <p>
            Hybrid search over approved/published enterprise knowledge with
            citations. Draft knowledge is never retrieved.
          </p>
        </section>

        <section className="panel">
          <form className="stack-form" onSubmit={onSearch}>
            <label>
              Query
              <textarea
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                rows={3}
                required
                placeholder="e.g. high-density Wi-Fi AP spacing guidance"
              />
            </label>
            <div className="form-row">
              <label>
                Domain filter
                <select
                  value={domainCode}
                  onChange={(e) => setDomainCode(e.target.value)}
                >
                  <option value="">All domains</option>
                  {domains.map((d) => (
                    <option key={d.code} value={d.code}>
                      {d.name}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Mode
                <select
                  value={mode}
                  onChange={(e) =>
                    setMode(e.target.value === "context" ? "context" : "search")
                  }
                >
                  <option value="search">Search hits</option>
                  <option value="context">Assembled context</option>
                </select>
              </label>
            </div>
            <button className="btn-primary" type="submit" disabled={busy}>
              {busy ? "Searching…" : "Search"}
            </button>
          </form>
          {error ? <p className="status status-error">{error}</p> : null}
        </section>

        {result ? (
          <section className="panel">
            <div className="panel-heading">
              <h2>Results</h2>
              <span className="muted">
                {result.embedding_provider}/{result.embedding_model} ·{" "}
                {result.latency_ms}ms · {result.hits?.length ?? 0} hits
              </span>
            </div>
            {result.insufficient_evidence ? (
              <p className="status status-error">
                {result.message || "INSUFFICIENT EVIDENCE — REVIEW REQUIRED"}
              </p>
            ) : null}
            {result.context_text ? (
              <pre className="knowledge-content">{result.context_text}</pre>
            ) : null}
            <div className="table-wrap" style={{ marginTop: "1rem" }}>
              <table className="data-table">
                <thead>
                  <tr>
                    <th>#</th>
                    <th>Title</th>
                    <th>Domain</th>
                    <th>Score</th>
                    <th>Excerpt</th>
                  </tr>
                </thead>
                <tbody>
                  {(result.hits || []).map((hit) => (
                    <tr key={hit.chunk_id}>
                      <td>{hit.rank}</td>
                      <td>
                        <Link
                          className="table-link"
                          href={`/knowledge/${hit.citation.knowledge_id}`}
                        >
                          {hit.citation.title}
                        </Link>
                        <div className="muted">
                          v{hit.citation.version_label}
                          {hit.citation.page_number != null
                            ? ` · p${hit.citation.page_number}`
                            : ""}
                        </div>
                      </td>
                      <td>{hit.citation.domain_code || "—"}</td>
                      <td>{(hit.fused_score ?? 0).toFixed(4)}</td>
                      <td style={{ maxWidth: "28rem" }}>
                        {(hit.citation.excerpt || hit.content).slice(0, 220)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        ) : null}
      </main>
    </div>
  );
}
