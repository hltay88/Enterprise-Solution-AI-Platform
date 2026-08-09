"use client";

import { useEffect, useState } from "react";

import { apiGet, ApiClientError } from "@/lib/api";
import type {
  ArchitectureOptionSummary,
  NamedCount,
  VendorAnalyticsBundle,
} from "@/lib/types";

type VendorAnalyticsPanelProps = {
  projectId: string;
  refreshToken?: number;
};

function formatRatio(value: number): string {
  return `${Math.round(value * 100)}%`;
}

function formatOptional(value: number | null | undefined, digits = 2): string {
  if (value === null || value === undefined) return "—";
  return value.toFixed(digits);
}

function CountList({
  title,
  items,
  empty = "None",
}: {
  title: string;
  items: NamedCount[];
  empty?: string;
}) {
  return (
    <div className="rkm-section">
      <h4>{title}</h4>
      {items.length === 0 ? (
        <p className="muted">{empty}</p>
      ) : (
        <ul className="rkm-list">
          {items.map((item) => (
            <li key={`${title}-${item.key}`} className="rkm-item">
              <span>
                {item.key.replace(/_/g, " ")}{" "}
                <span className="muted">× {item.count}</span>
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export function VendorAnalyticsPanel({
  projectId,
  refreshToken = 0,
}: VendorAnalyticsPanelProps) {
  const [bundle, setBundle] = useState<VendorAnalyticsBundle | null>(null);
  const [architectures, setArchitectures] = useState<ArchitectureOptionSummary[]>(
    [],
  );
  const [architectureId, setArchitectureId] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function load(architectureFilter?: string) {
    setLoading(true);
    setError(null);
    try {
      const archRows = await apiGet<ArchitectureOptionSummary[]>(
        `/api/v1/projects/${projectId}/architectures`,
        true,
      );
      setArchitectures(archRows);

      const query = architectureFilter
        ? `?architecture_id=${encodeURIComponent(architectureFilter)}`
        : "";
      const data = await apiGet<VendorAnalyticsBundle>(
        `/api/v1/projects/${projectId}/vendor-analytics${query}`,
        true,
      );
      setBundle(data);
    } catch (err) {
      if (err instanceof ApiClientError && err.status === 404) {
        setBundle(null);
        return;
      }
      setError(
        err instanceof ApiClientError
          ? err.message
          : "Unable to load vendor analytics",
      );
      setBundle(null);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load(architectureId || undefined);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId, refreshToken, architectureId]);

  const catalogue = bundle?.catalogue;
  const mappings = bundle?.mappings;
  const warnings = [
    ...(catalogue?.warnings ?? []),
    ...(mappings?.warnings ?? []),
  ];

  return (
    <section className="panel rkm-panel" id="vendor-analytics-panel">
      <div className="panel-heading">
        <div>
          <h2>Vendor analytics</h2>
          <p className="muted">
            Project fit dashboard: mapping coverage, fit-score distribution, and
            selected vs rejected — with catalogue freshness as context
            (ATLAS-035 / ATLAS-038).
          </p>
        </div>
        <label className="field-inline">
          <span className="muted">Architecture filter</span>
          <select
            value={architectureId}
            onChange={(event) => setArchitectureId(event.target.value)}
          >
            <option value="">All mappings in project</option>
            {architectures.map((item) => (
              <option key={item.id} value={item.id}>
                {item.title} ({item.candidate_key})
              </option>
            ))}
          </select>
        </label>
      </div>

      {error ? <p className="form-error">{error}</p> : null}
      {loading ? <p className="status">Loading…</p> : null}

      {!loading && !bundle ? (
        <div className="empty-state">
          <p>No vendor analytics available yet.</p>
          <p className="muted">
            Seed or import a catalogue, then map products on an architecture.
          </p>
        </div>
      ) : null}

      {bundle && catalogue && mappings ? (
        <>
          {warnings.length > 0 ? (
            <div className="rkm-section">
              <h3>Warnings</h3>
              <ul className="rkm-list">
                {warnings.map((warning) => (
                  <li key={warning} className="rkm-item">
                    <span className="form-error">{warning}</span>
                  </li>
                ))}
              </ul>
            </div>
          ) : null}

          <div className="rkm-section">
            <h3>Project fit</h3>
            <ul className="rkm-list">
              <li className="rkm-item">
                Component coverage:{" "}
                <strong>
                  {mappings.mapped_component_count} / {mappings.component_count}
                </strong>{" "}
                <span className="muted">
                  ({formatRatio(mappings.coverage_ratio)})
                </span>
              </li>
              <li className="rkm-item">
                Unmatched components:{" "}
                <strong>{mappings.unmatched_component_count}</strong>
              </li>
              <li className="rkm-item">
                Selected / candidate / rejected:{" "}
                <strong>
                  {mappings.selected_count} / {mappings.candidate_count} /{" "}
                  {mappings.rejected_count}
                </strong>
              </li>
              <li className="rkm-item">
                Mappings: <strong>{mappings.mapping_count}</strong>
              </li>
              <li className="rkm-item">
                Avg fit score (0–5):{" "}
                <strong>{formatOptional(mappings.average_fit_score, 1)}</strong>
              </li>
              <li className="rkm-item">
                Stale mapped SKUs:{" "}
                <strong>{mappings.stale_mapped_count}</strong>
              </li>
            </ul>
            <div className="architecture-compare-grid">
              <CountList
                title="Fit score distribution"
                items={mappings.fit_score_buckets ?? []}
                empty="No fit scores yet"
              />
              <CountList title="By status" items={mappings.by_status} />
              <CountList
                title="By preference"
                items={mappings.by_preference_kind}
              />
              <CountList title="By vendor" items={mappings.by_vendor} />
            </div>
            <div className="architecture-compare-grid">
              <CountList title="By lifecycle" items={mappings.by_lifecycle} />
            </div>
          </div>

          <div className="rkm-section">
            <h3>Catalogue freshness</h3>
            <p className="muted">
              {catalogue.catalogue_name || "Latest catalogue"}
              {catalogue.catalogue_id
                ? ` · ${catalogue.catalogue_id.slice(0, 8)}…`
                : ""}
            </p>
            <ul className="rkm-list">
              <li className="rkm-item">
                Products: <strong>{catalogue.product_count}</strong>
              </li>
              <li className="rkm-item">
                Stale: <strong>{catalogue.stale_count}</strong> (
                {formatRatio(catalogue.stale_ratio)})
              </li>
              <li className="rkm-item">
                Avg confidence:{" "}
                <strong>{formatOptional(catalogue.average_confidence, 2)}</strong>
              </li>
            </ul>
            <div className="architecture-compare-grid">
              <CountList title="By vendor" items={catalogue.by_vendor} />
              <CountList title="By category" items={catalogue.by_category} />
              <CountList title="By lifecycle" items={catalogue.by_lifecycle} />
              <CountList title="By region" items={catalogue.by_region} />
            </div>
          </div>
        </>
      ) : null}
    </section>
  );
}
