"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { AppHeader } from "@/components/AppHeader";
import { RequireAuth } from "@/components/RequireAuth";
import { apiGet, apiPost, ApiClientError } from "@/lib/api";
import type { TenantMember, TenantSummary } from "@/lib/types";

function TenantAdminContent({ userName }: { userName: string }) {
  const [tenants, setTenants] = useState<TenantSummary[]>([]);
  const [current, setCurrent] = useState<TenantSummary | null>(null);
  const [members, setMembers] = useState<TenantMember[]>([]);
  const [email, setEmail] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function load() {
    setError(null);
    try {
      const [list, cur] = await Promise.all([
        apiGet<TenantSummary[]>("/api/v1/tenants", true),
        apiGet<TenantSummary | null>("/api/v1/tenants/current", true),
      ]);
      setTenants(list);
      setCurrent(cur);
      if (cur?.id) {
        const memberRows = await apiGet<TenantMember[]>(
          `/api/v1/tenants/${cur.id}/members`,
          true,
        );
        setMembers(memberRows);
      }
    } catch (err) {
      setError(
        err instanceof ApiClientError ? err.message : "Unable to load tenants",
      );
    }
  }

  useEffect(() => {
    void load();
  }, []);

  async function invite() {
    if (!current?.id || !email.trim()) return;
    setBusy(true);
    setError(null);
    try {
      await apiPost(
        `/api/v1/tenants/${current.id}/members`,
        { email: email.trim(), role: "editor" },
        true,
      );
      setEmail("");
      await load();
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : "Invite failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="shell">
      <AppHeader userName={userName} showDashboardLink showKnowledgeLink />
      <main className="page">
        <section className="page-header">
          <p className="muted">
            <Link href="/dashboard">← Back to dashboard</Link>
          </p>
          <h1>Tenant admin</h1>
          <p>Sprint 5.5 — membership for the active tenant (Mac/local SaaS foundation).</p>
        </section>

        {error ? <p className="status status-error">{error}</p> : null}

        <section className="panel rkm-panel">
          <h2>Current tenant</h2>
          {current ? (
            <p>
              {current.name} <span className="muted">({current.slug})</span>
              {current.role ? ` · role ${current.role}` : ""}
            </p>
          ) : (
            <p className="muted">No active tenant.</p>
          )}
          {tenants.length > 1 ? (
            <ul>
              {tenants.map((t) => (
                <li key={t.id}>
                  {t.name} ({t.slug})
                </li>
              ))}
            </ul>
          ) : null}
        </section>

        <section className="panel rkm-panel">
          <h2>Members</h2>
          <ul>
            {members.map((m) => (
              <li key={m.membership_id}>
                {m.name} · {m.email} · {m.role}
              </li>
            ))}
          </ul>
          <label className="field">
            <span>Add existing user by email</span>
            <input
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="user@example.com"
            />
          </label>
          <button
            className="btn-primary btn-compact"
            type="button"
            disabled={busy || !email.trim()}
            onClick={() => void invite()}
          >
            Add member
          </button>
        </section>
      </main>
    </div>
  );
}

export default function TenantAdminPage() {
  return (
    <RequireAuth>
      {(user) => <TenantAdminContent userName={user.name} />}
    </RequireAuth>
  );
}
