"use client";

import { useEffect, useMemo, useState } from "react";

import { apiGet, ApiClientError } from "@/lib/api";
import type {
  ArchitectureOption,
  ArchitectureOptionSummary,
  ArchitectureScore,
} from "@/lib/types";

type ArchitectureComparePanelProps = {
  projectId: string;
  refreshToken?: number;
};

const MAX_COMPARE = 3;

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

function scoreByDimension(
  scores: ArchitectureScore[],
): Map<string, ArchitectureScore> {
  const map = new Map<string, ArchitectureScore>();
  for (const score of scores) {
    map.set(score.dimension, score);
  }
  return map;
}

export function ArchitectureComparePanel({
  projectId,
  refreshToken = 0,
}: ArchitectureComparePanelProps) {
  const [summaries, setSummaries] = useState<ArchitectureOptionSummary[]>([]);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [details, setDetails] = useState<ArchitectureOption[]>([]);
  const [loading, setLoading] = useState(true);
  const [comparing, setComparing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const latestBatch = useMemo(() => {
    if (!summaries.length) return [];
    const generationId = summaries[0]?.generation_id;
    const batch = summaries.filter((item) => item.generation_id === generationId);
    return batch.length ? batch : summaries;
  }, [summaries]);

  async function loadSummaries() {
    setLoading(true);
    setError(null);
    try {
      const rows = await apiGet<ArchitectureOptionSummary[]>(
        `/api/v1/projects/${projectId}/architectures`,
        true,
      );
      setSummaries(rows);
      // Default: select up to 3 from latest generation for a one-click compare.
      const generationId = rows[0]?.generation_id;
      const batch = generationId
        ? rows.filter((item) => item.generation_id === generationId)
        : rows;
      const defaults = batch.slice(0, MAX_COMPARE).map((item) => item.id);
      setSelectedIds(defaults);
      if (defaults.length >= 2) {
        await loadDetails(defaults);
      } else {
        setDetails([]);
      }
    } catch (err) {
      if (err instanceof ApiClientError && err.status === 404) {
        setSummaries([]);
        setDetails([]);
        return;
      }
      setError(
        err instanceof ApiClientError
          ? err.message
          : "Unable to load architecture candidates",
      );
    } finally {
      setLoading(false);
    }
  }

  async function loadDetails(ids: string[]) {
    setComparing(true);
    setError(null);
    try {
      const loaded = await Promise.all(
        ids.map((id) =>
          apiGet<ArchitectureOption>(
            `/api/v1/projects/${projectId}/architectures/${id}`,
            true,
          ),
        ),
      );
      // Preserve selection order.
      const byId = new Map(loaded.map((item) => [item.id, item]));
      setDetails(ids.map((id) => byId.get(id)).filter(Boolean) as ArchitectureOption[]);
    } catch (err) {
      setError(
        err instanceof ApiClientError
          ? err.message
          : "Unable to load candidates for comparison",
      );
      setDetails([]);
    } finally {
      setComparing(false);
    }
  }

  useEffect(() => {
    void loadSummaries();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId, refreshToken]);

  function toggleId(id: string) {
    setSelectedIds((current) => {
      if (current.includes(id)) {
        return current.filter((item) => item !== id);
      }
      if (current.length >= MAX_COMPARE) {
        return [...current.slice(1), id];
      }
      return [...current, id];
    });
  }

  async function compare() {
    if (selectedIds.length < 2) {
      setError("Select at least two candidates to compare");
      return;
    }
    await loadDetails(selectedIds);
  }

  const dimensions = useMemo(() => {
    const set = new Set<string>();
    for (const option of details) {
      for (const score of option.scores) {
        set.add(score.dimension);
      }
    }
    return Array.from(set);
  }, [details]);

  return (
    <section className="panel rkm-panel" id="architecture-compare-panel">
      <div className="panel-heading">
        <div>
          <h2>Compare architectures</h2>
          <p className="muted">
            Side-by-side review of candidates from the latest generation (scores,
            coverage signals, trade-offs). Select up to {MAX_COMPARE}.
          </p>
        </div>
        <button
          className="btn-primary btn-compact"
          type="button"
          disabled={comparing || selectedIds.length < 2}
          onClick={() => void compare()}
        >
          {comparing ? "Comparing…" : "Compare selected"}
        </button>
      </div>

      {error ? <p className="form-error">{error}</p> : null}
      {loading ? <p className="status">Loading…</p> : null}

      {!loading && latestBatch.length === 0 ? (
        <div className="empty-state">
          <p>No architecture candidates to compare yet.</p>
          <p className="muted">
            Generate candidates in the Architecture panel first.
          </p>
        </div>
      ) : null}

      {latestBatch.length > 0 ? (
        <div className="rkm-section">
          <h3>Candidates (latest generation)</h3>
          <ul className="rkm-list architecture-candidate-list">
            {latestBatch.map((item) => {
              const checked = selectedIds.includes(item.id);
              return (
                <li key={item.id} className="rkm-item">
                  <label className="architecture-compare-pick">
                    <input
                      type="checkbox"
                      checked={checked}
                      onChange={() => toggleId(item.id)}
                    />
                    <span>
                      <strong>
                        {item.title}{" "}
                        <span className="muted">({item.candidate_key})</span>
                      </strong>
                      <span className="muted">
                        {" "}
                        · {item.status.replace(/_/g, " ")} · score{" "}
                        {formatScore(item.overall_score)} · confidence{" "}
                        {formatConfidence(item.confidence)}
                      </span>
                    </span>
                  </label>
                </li>
              );
            })}
          </ul>
        </div>
      ) : null}

      {details.length >= 2 ? (
        <div className="rkm-section architecture-compare-wrap">
          <h3>Comparison</h3>
          <div className="architecture-compare-scroll">
            <table className="architecture-compare-table">
              <thead>
                <tr>
                  <th scope="col">Dimension</th>
                  {details.map((option) => (
                    <th key={option.id} scope="col">
                      {option.title}
                      <div className="muted">
                        {option.candidate_key} ·{" "}
                        {option.status.replace(/_/g, " ")}
                      </div>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                <tr>
                  <th scope="row">Overall score</th>
                  {details.map((option) => (
                    <td key={`${option.id}-overall`}>
                      {formatScore(option.overall_score)}
                    </td>
                  ))}
                </tr>
                <tr>
                  <th scope="row">Confidence</th>
                  {details.map((option) => (
                    <td key={`${option.id}-conf`}>
                      {formatConfidence(option.confidence)}
                    </td>
                  ))}
                </tr>
                <tr>
                  <th scope="row">Patterns</th>
                  {details.map((option) => (
                    <td key={`${option.id}-patterns`}>
                      {option.pattern_codes.join(", ") || "—"}
                    </td>
                  ))}
                </tr>
                <tr>
                  <th scope="row">Components</th>
                  {details.map((option) => (
                    <td key={`${option.id}-components`}>
                      {option.components.length}
                    </td>
                  ))}
                </tr>
                <tr>
                  <th scope="row">Risks</th>
                  {details.map((option) => (
                    <td key={`${option.id}-risks`}>{option.risks.length}</td>
                  ))}
                </tr>
                <tr>
                  <th scope="row">Assumptions</th>
                  {details.map((option) => (
                    <td key={`${option.id}-assumptions`}>
                      {option.assumptions.length}
                    </td>
                  ))}
                </tr>
                <tr>
                  <th scope="row">Open capacity questions</th>
                  {details.map((option) => (
                    <td key={`${option.id}-capacity`}>
                      {
                        option.capacity_notes.filter((note) => note.open_question)
                          .length
                      }
                    </td>
                  ))}
                </tr>
                {dimensions.map((dimension) => {
                  const maps = details.map((option) =>
                    scoreByDimension(option.scores),
                  );
                  return (
                    <tr key={dimension}>
                      <th scope="row">Score · {formatDimension(dimension)}</th>
                      {details.map((option, index) => {
                        const score = maps[index].get(dimension);
                        return (
                          <td key={`${option.id}-${dimension}`}>
                            {score
                              ? `${score.score}/5 · w${Math.round(score.weight * 100)}%`
                              : "—"}
                            {score?.explanation ? (
                              <div className="muted">{score.explanation}</div>
                            ) : null}
                          </td>
                        );
                      })}
                    </tr>
                  );
                })}
                <tr>
                  <th scope="row">Advantages</th>
                  {details.map((option) => (
                    <td key={`${option.id}-adv`}>
                      {option.advantages.length ? (
                        <ul className="architecture-compare-bullets">
                          {option.advantages.map((item) => (
                            <li key={item}>{item}</li>
                          ))}
                        </ul>
                      ) : (
                        "—"
                      )}
                    </td>
                  ))}
                </tr>
                <tr>
                  <th scope="row">Disadvantages</th>
                  {details.map((option) => (
                    <td key={`${option.id}-dis`}>
                      {option.disadvantages.length ? (
                        <ul className="architecture-compare-bullets">
                          {option.disadvantages.map((item) => (
                            <li key={item}>{item}</li>
                          ))}
                        </ul>
                      ) : (
                        "—"
                      )}
                    </td>
                  ))}
                </tr>
                <tr>
                  <th scope="row">Summary</th>
                  {details.map((option) => (
                    <td key={`${option.id}-summary`}>
                      {option.summary || "—"}
                    </td>
                  ))}
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      ) : null}
    </section>
  );
}
