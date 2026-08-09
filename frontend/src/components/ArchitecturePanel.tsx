"use client";

import { useEffect, useState } from "react";

import { apiGet, apiPost, ApiClientError } from "@/lib/api";
import type {
  ArchitectureGenerateResult,
  ArchitectureOption,
  ArchitectureOptionSummary,
} from "@/lib/types";

type ArchitecturePanelProps = {
  projectId: string;
  refreshToken?: number;
};

type PanelState =
  | { kind: "loading" }
  | { kind: "empty" }
  | {
      kind: "ready";
      options: ArchitectureOptionSummary[];
      selected: ArchitectureOption;
    }
  | { kind: "error"; message: string };

function formatConfidence(value: number): string {
  const pct = value > 1 ? value : value * 100;
  return `${Math.round(pct)}%`;
}

function formatScore(value: number | null | undefined): string {
  if (value === null || value === undefined) return "—";
  return value.toFixed(1);
}

function formatDimension(value: string): string {
  return value.replace(/_/g, " ");
}

export function ArchitecturePanel({
  projectId,
  refreshToken = 0,
}: ArchitecturePanelProps) {
  const [state, setState] = useState<PanelState>({ kind: "loading" });
  const [running, setRunning] = useState(false);
  const [selecting, setSelecting] = useState(false);
  const [runError, setRunError] = useState<string | null>(null);

  async function loadDetail(
    options: ArchitectureOptionSummary[],
    preferredId?: string,
  ) {
    if (!options.length) {
      setState({ kind: "empty" });
      return;
    }
    const preferred =
      options.find((item) => item.id === preferredId) ||
      options.find((item) => item.candidate_key === "standard") ||
      options[0];
    const selected = await apiGet<ArchitectureOption>(
      `/api/v1/projects/${projectId}/architectures/${preferred.id}`,
      true,
    );
    setState({ kind: "ready", options, selected });
  }

  async function load() {
    try {
      const options = await apiGet<ArchitectureOptionSummary[]>(
        `/api/v1/projects/${projectId}/architectures`,
        true,
      );
      if (!options.length) {
        setState({ kind: "empty" });
        return;
      }
      await loadDetail(options);
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
            : "Unable to load architecture candidates",
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
      const result = await apiPost<ArchitectureGenerateResult>(
        `/api/v1/projects/${projectId}/architectures/generate`,
        {},
        true,
      );
      const options = await apiGet<ArchitectureOptionSummary[]>(
        `/api/v1/projects/${projectId}/architectures`,
        true,
      );
      const preferredId =
        result.architectures.find((item) => item.candidate_key === "standard")
          ?.id || result.architectures[0]?.id;
      await loadDetail(options, preferredId);
    } catch (err) {
      setRunError(
        err instanceof ApiClientError
          ? err.message
          : "Unable to generate architecture candidates",
      );
    } finally {
      setRunning(false);
    }
  }

  async function selectOption(optionId: string) {
    if (state.kind !== "ready" || state.selected.id === optionId) return;
    setSelecting(true);
    setRunError(null);
    try {
      const selected = await apiGet<ArchitectureOption>(
        `/api/v1/projects/${projectId}/architectures/${optionId}`,
        true,
      );
      setState({ kind: "ready", options: state.options, selected });
    } catch (err) {
      setRunError(
        err instanceof ApiClientError
          ? err.message
          : "Unable to load architecture candidate",
      );
    } finally {
      setSelecting(false);
    }
  }

  return (
    <section className="panel rkm-panel" id="architecture-panel">
      <div className="panel-heading">
        <div>
          <h2>Architecture candidates</h2>
          <p className="muted">
            Phase 3 — reviewable options from Published RKM + latest domain
            analysis (vendor-neutral; no approve yet)
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
              ? "Regenerate candidates"
              : "Generate candidates"}
        </button>
      </div>

      {runError ? <p className="form-error">{runError}</p> : null}
      {state.kind === "loading" ? <p className="status">Loading…</p> : null}
      {state.kind === "empty" ? (
        <div className="empty-state">
          <p>No architecture candidates yet.</p>
          <p className="muted">
            Publish an RKM, run solution domain analysis, then generate
            candidates here.
          </p>
        </div>
      ) : null}
      {state.kind === "error" ? (
        <p className="status status-error">{state.message}</p>
      ) : null}

      {state.kind === "ready" ? (
        <>
          <CandidatePicker
            options={state.options}
            selectedId={state.selected.id}
            disabled={selecting || running}
            onSelect={(id) => void selectOption(id)}
          />
          {selecting ? <p className="status">Loading candidate…</p> : null}
          <ArchitectureOptionView option={state.selected} />
        </>
      ) : null}
    </section>
  );
}

function CandidatePicker({
  options,
  selectedId,
  disabled,
  onSelect,
}: {
  options: ArchitectureOptionSummary[];
  selectedId: string;
  disabled: boolean;
  onSelect: (id: string) => void;
}) {
  // Prefer latest generation batch for the picker.
  const latestGenerationId = options[0]?.generation_id;
  const latestBatch = options.filter(
    (item) => item.generation_id === latestGenerationId,
  );
  const shown = latestBatch.length ? latestBatch : options;

  return (
    <div className="rkm-section">
      <h3>Candidates</h3>
      <ul className="rkm-list architecture-candidate-list">
        {shown.map((item) => {
          const active = item.id === selectedId;
          return (
            <li key={item.id} className="rkm-item">
              <button
                type="button"
                className={
                  active
                    ? "architecture-candidate-btn is-active"
                    : "architecture-candidate-btn"
                }
                disabled={disabled}
                onClick={() => onSelect(item.id)}
              >
                <span className="rkm-item-head">
                  <strong>
                    {item.title}{" "}
                    <span className="muted">({item.candidate_key})</span>
                  </strong>
                  <span className="muted">
                    score {formatScore(item.overall_score)} · confidence{" "}
                    {formatConfidence(item.confidence)} · v{item.version_label}
                  </span>
                </span>
                {item.summary ? <p className="muted">{item.summary}</p> : null}
                {item.pattern_codes.length > 0 ? (
                  <p className="muted">
                    Patterns: {item.pattern_codes.join(", ")}
                  </p>
                ) : null}
              </button>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

function ArchitectureOptionView({ option }: { option: ArchitectureOption }) {
  return (
    <>
      <div className="rkm-meta muted">
        <span>
          {option.title} · v{option.version_label}
        </span>
        <span>
          {" "}
          · from Published RKM v{option.rkm_version_label || "—"}
        </span>
        {option.domain_analysis_id ? (
          <span> · domain analysis pinned</span>
        ) : null}
        {option.model ? <span> · Model {option.model}</span> : null}
        {option.knowledge_pack_version ? (
          <span> · Pack {option.knowledge_pack_version}</span>
        ) : null}
        <span>
          {" "}
          · overall {formatScore(option.overall_score)} / confidence{" "}
          {formatConfidence(option.confidence)}
        </span>
      </div>
      {option.summary ? <p>{option.summary}</p> : null}
      {option.reasoning_summary ? (
        <p className="rkm-reasoning">{option.reasoning_summary}</p>
      ) : null}

      {option.pattern_codes.length > 0 ? (
        <div className="rkm-section">
          <h3>Patterns</h3>
          <p>{option.pattern_codes.join(", ")}</p>
        </div>
      ) : null}

      <StringList title="High-level architecture" items={option.high_level_architecture} />
      <StringList title="Logical architecture" items={option.logical_architecture} />
      <StringList title="Physical architecture" items={option.physical_architecture} />

      {option.technology_stack.length > 0 ? (
        <div className="rkm-section">
          <h3>Technology stack (categories)</h3>
          <ul className="rkm-list">
            {option.technology_stack.map((item, index) => (
              <li
                key={`${String(item.layer)}-${String(item.category)}-${index}`}
                className="rkm-item"
              >
                <strong>
                  {String(item.layer || "Layer")}:{" "}
                  {String(item.category || "Category")}
                </strong>
                {item.rationale ? (
                  <p className="muted">{String(item.rationale)}</p>
                ) : null}
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      <div className="rkm-section">
        <h3>Components</h3>
        {option.components.length === 0 ? (
          <p className="muted">No components recorded.</p>
        ) : (
          <ul className="rkm-list">
            {option.components.map((component) => (
              <li key={component.id} className="rkm-item">
                <div className="rkm-item-head">
                  <strong>{component.name}</strong>
                  <span className="muted">{component.component_kind}</span>
                </div>
                {component.purpose ? <p>{component.purpose}</p> : null}
                {component.maps_to_requirements.length > 0 ? (
                  <div className="rkm-evidence">
                    {component.maps_to_requirements.map((reqId) => (
                      <span key={reqId} className="rkm-evidence-chip">
                        {reqId}
                      </span>
                    ))}
                  </div>
                ) : null}
              </li>
            ))}
          </ul>
        )}
      </div>

      {option.decisions.length > 0 ? (
        <div className="rkm-section">
          <h3>Design decisions</h3>
          <ul className="rkm-list">
            {option.decisions.map((item) => (
              <li key={item.id} className="rkm-item">
                <strong>{item.decision}</strong>
                {item.rationale ? <p>{item.rationale}</p> : null}
                {item.impact ? (
                  <p className="muted">Impact: {item.impact}</p>
                ) : null}
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      <div className="rkm-section">
        <h3>Scores</h3>
        {option.scores.length === 0 ? (
          <p className="muted">No scores recorded.</p>
        ) : (
          <ul className="rkm-list">
            {option.scores.map((score) => (
              <li key={score.id} className="rkm-item">
                <div className="rkm-item-head">
                  <strong>{formatDimension(score.dimension)}</strong>
                  <span className="muted">
                    {score.score}/5 · weight {Math.round(score.weight * 100)}%
                  </span>
                </div>
                <p className="muted">{score.explanation}</p>
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className="rkm-section">
        <h3>Assumptions</h3>
        {option.assumptions.length === 0 ? (
          <p className="muted">No assumptions recorded.</p>
        ) : (
          <ul className="rkm-list">
            {option.assumptions.map((item) => (
              <li key={item.id} className="rkm-item">
                <div className="rkm-item-head">
                  <strong>{item.statement}</strong>
                  <span className="muted">{item.status}</span>
                </div>
                {item.reason ? <p className="muted">{item.reason}</p> : null}
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className="rkm-section">
        <h3>Risks</h3>
        {option.risks.length === 0 ? (
          <p className="muted">No risks recorded.</p>
        ) : (
          <ul className="rkm-list">
            {option.risks.map((item) => (
              <li key={item.id} className="rkm-item">
                <div className="rkm-item-head">
                  <strong>{item.description}</strong>
                  <span className="muted">
                    {item.category} · {item.probability}/{item.severity}
                  </span>
                </div>
                {item.mitigation ? (
                  <p className="muted">Mitigation: {item.mitigation}</p>
                ) : null}
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className="rkm-section">
        <h3>Capacity notes</h3>
        {option.capacity_notes.length === 0 ? (
          <p className="muted">No capacity notes recorded.</p>
        ) : (
          <ul className="rkm-list">
            {option.capacity_notes.map((note) => (
              <li key={note.id} className="rkm-item">
                <div className="rkm-item-head">
                  <strong>{note.label}</strong>
                  <span className="muted">
                    confidence {formatConfidence(note.confidence)}
                  </span>
                </div>
                {note.result ? <p>Result: {note.result}</p> : null}
                {note.open_question ? (
                  <p className="muted">Open: {note.open_question}</p>
                ) : null}
                {note.method || note.input_value ? (
                  <p className="muted">
                    {[note.input_value, note.unit, note.method]
                      .filter(Boolean)
                      .join(" · ")}
                  </p>
                ) : null}
              </li>
            ))}
          </ul>
        )}
      </div>

      <StringList title="Advantages" items={option.advantages} />
      <StringList title="Disadvantages" items={option.disadvantages} />
    </>
  );
}

function StringList({ title, items }: { title: string; items: string[] }) {
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
