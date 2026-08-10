"use client";

import { useEffect, useState } from "react";

import { apiGet, apiPost, ApiClientError } from "@/lib/api";
import type {
  AgentRunDetail,
  AgentRunSummary,
  AgentSummary,
  SpecialistOutput,
} from "@/lib/types";

type AgentWorkspacePanelProps = {
  projectId: string;
  refreshToken?: number;
};

function formatPct(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return "—";
  const pct = value > 1 ? value : value * 100;
  return `${Math.round(pct)}%`;
}

function SpecialistCard({ specialist }: { specialist: SpecialistOutput }) {
  return (
    <article className="empty-state">
      <header className="panel-heading">
        <div>
          <h3>{specialist.agent_id}</h3>
          <p className="muted">
            {specialist.status} · {formatPct(specialist.confidence)}
          </p>
        </div>
      </header>
      <p>{specialist.summary}</p>
      {specialist.recommendations.length > 0 ? (
        <div>
          <p className="muted">Recommendations</p>
          <ul>
            {specialist.recommendations.slice(0, 4).map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>
      ) : null}
      {specialist.findings.length > 0 ? (
        <div>
          <p className="muted">Findings</p>
          <ul>
            {specialist.findings.slice(0, 4).map((f) => (
              <li key={f.code}>
                [{f.severity}] {f.statement}
              </li>
            ))}
          </ul>
        </div>
      ) : null}
      {specialist.citations.length > 0 ? (
        <div>
          <p className="muted">Citations</p>
          <ul>
            {specialist.citations.slice(0, 3).map((c, idx) => (
              <li key={`${c.chunk_id ?? c.title}-${idx}`}>
                {c.title}
                {c.excerpt ? ` — ${c.excerpt.slice(0, 120)}` : ""}
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </article>
  );
}

export function AgentWorkspacePanel({
  projectId,
  refreshToken = 0,
}: AgentWorkspacePanelProps) {
  const [agents, setAgents] = useState<AgentSummary[]>([]);
  const [runs, setRuns] = useState<AgentRunSummary[]>([]);
  const [detail, setDetail] = useState<AgentRunDetail | null>(null);
  const [goal, setGoal] = useState("");
  const [selected, setSelected] = useState<string[]>([]);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const [agentRows, runRows] = await Promise.all([
        apiGet<AgentSummary[]>("/api/v1/agents", true),
        apiGet<AgentRunSummary[]>(`/api/v1/projects/${projectId}/agent-runs`, true),
      ]);
      setAgents(agentRows);
      setRuns(runRows);
      const runnable = agentRows.filter((a) => a.runnable).map((a) => a.id);
      setSelected((prev) => (prev.length ? prev : runnable));
      if (runRows[0] && !detail) {
        const latest = await apiGet<AgentRunDetail>(
          `/api/v1/agent-runs/${runRows[0].id}`,
          true,
        );
        setDetail(latest);
      }
    } catch (err) {
      setError(
        err instanceof ApiClientError
          ? err.message
          : "Unable to load agent workspace",
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId, refreshToken]);

  function toggleAgent(id: string) {
    setSelected((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id],
    );
  }

  async function runAgents() {
    setRunning(true);
    setError(null);
    try {
      const result = await apiPost<AgentRunDetail>(
        `/api/v1/projects/${projectId}/agent-runs`,
        {
          goal: goal.trim() || null,
          include_agents: selected,
        },
        true,
      );
      setDetail(result);
      const runRows = await apiGet<AgentRunSummary[]>(
        `/api/v1/projects/${projectId}/agent-runs`,
        true,
      );
      setRuns(runRows);
    } catch (err) {
      setError(
        err instanceof ApiClientError
          ? err.message
          : "Unable to run specialist agents",
      );
    } finally {
      setRunning(false);
    }
  }

  async function openRun(runId: string) {
    setError(null);
    try {
      const result = await apiGet<AgentRunDetail>(`/api/v1/agent-runs/${runId}`, true);
      setDetail(result);
    } catch (err) {
      setError(
        err instanceof ApiClientError ? err.message : "Unable to load agent run",
      );
    }
  }

  const runnableAgents = agents.filter((a) => a.runnable);
  const stubAgents = agents.filter((a) => !a.runnable);

  return (
    <section className="panel rkm-panel" id="agent-workspace-panel">
      <div className="panel-heading">
        <div>
          <h2>Agent workspace</h2>
          <p className="muted">
            Sprint 5.3 — advise-only specialist assessments (cannot approve RKM or
            architecture)
          </p>
        </div>
        <button
          className="btn-primary btn-compact"
          type="button"
          onClick={() => void runAgents()}
          disabled={running || selected.length === 0}
        >
          {running ? "Running…" : "Run specialists"}
        </button>
      </div>

      {error ? <p className="form-error">{error}</p> : null}
      {loading ? <p className="status">Loading agents…</p> : null}

      {!loading ? (
        <>
          <label className="field">
            <span>Goal (optional)</span>
            <input
              type="text"
              value={goal}
              onChange={(e) => setGoal(e.target.value)}
              placeholder="e.g. Validate campus Wi-Fi + security posture gaps"
            />
          </label>

          <div>
            <p className="muted">Runnable specialists</p>
            {runnableAgents.map((agent) => (
              <label key={agent.id} style={{ display: "flex", gap: "0.5rem", alignItems: "center", marginBottom: "0.35rem" }}>
                <input
                  type="checkbox"
                  checked={selected.includes(agent.id)}
                  onChange={() => toggleAgent(agent.id)}
                />
                <span>
                  {agent.name}{" "}
                  <span className="muted">({agent.domain_code})</span>
                </span>
              </label>
            ))}
          </div>

          {stubAgents.length > 0 ? (
            <p className="muted">
              Coming soon: {stubAgents.map((a) => a.name).join(", ")}
            </p>
          ) : null}

          {detail ? (
            <div className="rkm-section">
              <div className="panel-heading">
                <div>
                  <h3>Latest run</h3>
                  <p className="muted">
                    {detail.status} · confidence {formatPct(detail.overall_confidence)} ·{" "}
                    {detail.conflict_count} conflict(s)
                    {detail.review_required ? " · REVIEW REQUIRED" : ""}
                  </p>
                </div>
              </div>

              {detail.conflicts.length > 0 ? (
                <div className="empty-state">
                  <p>Conflicts / trade-offs</p>
                  <ul>
                    {detail.conflicts.map((c) => (
                      <li key={c.code}>
                        [{c.severity}] {c.summary}{" "}
                        <span className="muted">({c.agents.join(", ")})</span>
                      </li>
                    ))}
                  </ul>
                </div>
              ) : null}

              <div style={{ display: "grid", gap: "1rem" }}>
                {detail.specialists.map((s) => (
                  <SpecialistCard key={s.agent_id} specialist={s} />
                ))}
              </div>

              {detail.tool_calls.length > 0 ? (
                <details>
                  <summary className="muted">
                    Tool calls ({detail.tool_calls.length})
                  </summary>
                  <ul>
                    {detail.tool_calls.map((t) => (
                      <li key={t.id}>
                        {t.agent_id ?? "orchestrator"} · {t.tool_name} ·{" "}
                        {t.ok ? "ok" : "failed"}
                        {t.latency_ms != null ? ` · ${t.latency_ms}ms` : ""}
                      </li>
                    ))}
                  </ul>
                </details>
              ) : null}
            </div>
          ) : (
            <div className="empty-state">
              <p>No agent runs yet.</p>
              <p className="muted">
                Select specialists and run an advisory assessment grounded on RKM,
                domains, and published knowledge.
              </p>
            </div>
          )}

          {runs.length > 1 ? (
            <div className="rkm-section">
              <p className="muted">Previous runs</p>
              <ul>
                {runs.slice(0, 8).map((run) => (
                  <li key={run.id}>
                    <button
                      type="button"
                      className="btn-secondary btn-compact"
                      onClick={() => void openRun(run.id)}
                    >
                      {new Date(run.created_at).toLocaleString()} — {run.status} (
                      {formatPct(run.overall_confidence)})
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
        </>
      ) : null}
    </section>
  );
}
