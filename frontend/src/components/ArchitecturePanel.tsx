"use client";

import { useEffect, useState } from "react";

import { apiGet, apiPost, ApiClientError } from "@/lib/api";
import type { ArchitectureRecommendation } from "@/lib/types";

type ArchitecturePanelProps = {
  projectId: string;
  refreshToken?: number;
};

type PanelState =
  | { kind: "loading" }
  | { kind: "empty" }
  | { kind: "ready"; architecture: ArchitectureRecommendation }
  | { kind: "error"; message: string };

export function ArchitecturePanel({
  projectId,
  refreshToken = 0,
}: ArchitecturePanelProps) {
  const [state, setState] = useState<PanelState>({ kind: "loading" });
  const [running, setRunning] = useState(false);
  const [runError, setRunError] = useState<string | null>(null);

  async function load() {
    try {
      const architecture = await apiGet<ArchitectureRecommendation>(
        `/api/v1/projects/${projectId}/architecture`,
        true,
      );
      setState({ kind: "ready", architecture });
    } catch (err) {
      if (err instanceof ApiClientError && err.status === 404) {
        setState({ kind: "empty" });
        return;
      }
      setState({
        kind: "error",
        message:
          err instanceof ApiClientError
            ? err.message
            : "Unable to load architecture",
      });
    }
  }

  useEffect(() => {
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId, refreshToken]);

  async function generate() {
    setRunning(true);
    setRunError(null);
    try {
      const architecture = await apiPost<ArchitectureRecommendation>(
        `/api/v1/projects/${projectId}/architecture/generate`,
        {},
        true,
      );
      setState({ kind: "ready", architecture });
    } catch (err) {
      setRunError(
        err instanceof ApiClientError
          ? err.message
          : "Unable to generate architecture",
      );
    } finally {
      setRunning(false);
    }
  }

  return (
    <section className="panel rkm-panel" id="architecture-panel">
      <div className="panel-heading">
        <div>
          <h2>Architecture recommendation</h2>
          <p className="muted">
            Phase 3 — generated only from a Published Requirement Knowledge Model
            (vendor-neutral)
          </p>
        </div>
        <button
          className="btn-primary btn-compact"
          type="button"
          onClick={() => void generate()}
          disabled={running}
        >
          {running
            ? "Generating…"
            : state.kind === "ready"
              ? "Regenerate architecture"
              : "Generate architecture"}
        </button>
      </div>

      {runError ? <p className="form-error">{runError}</p> : null}
      {state.kind === "loading" ? <p className="status">Loading…</p> : null}
      {state.kind === "empty" ? (
        <div className="empty-state">
          <p>No architecture recommendation yet.</p>
          <p className="muted">
            Publish an RKM first (Stage E), then generate architecture here.
          </p>
        </div>
      ) : null}
      {state.kind === "error" ? (
        <p className="status status-error">{state.message}</p>
      ) : null}

      {state.kind === "ready" ? (
        <>
          <div className="rkm-meta muted">
            <span>Architecture v{state.architecture.version_label}</span>
            <span>
              {" "}
              · from Published RKM v{state.architecture.rkm_version_label || "—"}
            </span>
            {state.architecture.model ? (
              <span> · Model {state.architecture.model}</span>
            ) : null}
          </div>
          <p>{state.architecture.summary}</p>
          {state.architecture.reasoning_summary ? (
            <p className="rkm-reasoning">{state.architecture.reasoning_summary}</p>
          ) : null}

          <ArchitectureList
            title="High-level architecture"
            items={state.architecture.high_level_architecture}
          />
          <ArchitectureList
            title="Logical architecture"
            items={state.architecture.logical_architecture}
          />
          <ArchitectureList
            title="Physical architecture"
            items={state.architecture.physical_architecture}
          />

          {state.architecture.technology_stack.length > 0 ? (
            <div className="rkm-section">
              <h3>Technology stack (categories)</h3>
              <ul className="rkm-list">
                {state.architecture.technology_stack.map((item, index) => (
                  <li key={`${item.layer}-${item.category}-${index}`} className="rkm-item">
                    <strong>
                      {item.layer}: {item.category}
                    </strong>
                    {item.rationale ? <p className="muted">{item.rationale}</p> : null}
                  </li>
                ))}
              </ul>
            </div>
          ) : null}

          {state.architecture.architecture_decisions.length > 0 ? (
            <div className="rkm-section">
              <h3>Architecture decisions</h3>
              <ul className="rkm-list">
                {state.architecture.architecture_decisions.map((item, index) => (
                  <li key={`${item.decision}-${index}`} className="rkm-item">
                    <strong>{item.decision}</strong>
                    {item.rationale ? <p>{item.rationale}</p> : null}
                    {item.impact ? <p className="muted">Impact: {item.impact}</p> : null}
                  </li>
                ))}
              </ul>
            </div>
          ) : null}

          <ArchitectureList
            title="Design assumptions"
            items={state.architecture.design_assumptions}
          />
          <ArchitectureList
            title="Technical risks"
            items={state.architecture.technical_risks}
          />

          {state.architecture.alternatives.length > 0 ? (
            <div className="rkm-section">
              <h3>Alternatives</h3>
              <ul className="rkm-list">
                {state.architecture.alternatives.map((item, index) => (
                  <li key={`${item.name}-${index}`} className="rkm-item">
                    <strong>{item.name}</strong>
                    {item.summary ? <p>{item.summary}</p> : null}
                    {item.tradeoffs ? (
                      <p className="muted">Tradeoffs: {item.tradeoffs}</p>
                    ) : null}
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

function ArchitectureList({ title, items }: { title: string; items: string[] }) {
  if (!items.length) return null;
  return (
    <div className="rkm-section">
      <h3>{title}</h3>
      <ul className="rkm-list">
        {items.map((item) => (
          <li key={item} className="rkm-item">
            <p>{item}</p>
          </li>
        ))}
      </ul>
    </div>
  );
}
