"use client";

import { useEffect, useState } from "react";

import { apiGet, apiPost, ApiClientError } from "@/lib/api";
import type { DocumentPackage, PackageExport, PackageValidation } from "@/lib/types";

type PackagePanelProps = {
  projectId: string;
  refreshToken?: number;
};

export function PackagePanel({
  projectId,
  refreshToken = 0,
}: PackagePanelProps) {
  const [packages, setPackages] = useState<DocumentPackage[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [validation, setValidation] = useState<PackageValidation | null>(null);
  const [exportResult, setExportResult] = useState<PackageExport | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [note, setNote] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const rows = await apiGet<DocumentPackage[]>(
        `/api/v1/projects/${projectId}/packages`,
        true,
      );
      setPackages(rows);
      if (rows.length && !selectedId) {
        setSelectedId(rows[0].id);
      }
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : "Failed to load");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId, refreshToken]);

  const selected = packages.find((p) => p.id === selectedId) || null;

  async function run(action: string, fn: () => Promise<void>) {
    setBusy(action);
    setError(null);
    setNote(null);
    try {
      await fn();
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : String(err));
    } finally {
      setBusy(null);
    }
  }

  return (
    <section className="form-panel">
      <h2>Document Package</h2>
      <p className="muted">
        Assemble approved proposal, presentation, SOW, solution design + validated
        BOM into a ZIP package (Sprint 4.4 / ATLAS-050). Assembly fails if any
        required deliverable is missing or architectures diverge.
      </p>

      {loading ? <p>Loading…</p> : null}
      {error ? <p className="error-text">{error}</p> : null}
      {note ? <p className="muted">{note}</p> : null}

      <div className="button-row" style={{ gap: 8, flexWrap: "wrap" }}>
        <button
          type="button"
          className="btn-primary"
          disabled={!!busy}
          onClick={() =>
            void run("assemble", async () => {
              const pkg = await apiPost<DocumentPackage>(
                `/api/v1/projects/${projectId}/packages/assemble`,
                {},
                true,
              );
              setSelectedId(pkg.id);
              setNote(`Assembled package: ${pkg.title} (${pkg.status})`);
              await load();
            })
          }
        >
          {busy === "assemble" ? "Assembling…" : "Assemble package"}
        </button>
        <button
          type="button"
          className="btn-secondary"
          disabled={!!busy || !selectedId}
          onClick={() =>
            void run("validate", async () => {
              const result = await apiPost<PackageValidation>(
                `/api/v1/projects/${projectId}/packages/${selectedId}/validate`,
                {},
                true,
              );
              setValidation(result);
              setNote(
                result.ok
                  ? "Package validation passed"
                  : "Package validation has issues",
              );
              await load();
            })
          }
        >
          Validate package
        </button>
        <button
          type="button"
          className="btn-secondary"
          disabled={!!busy || !selectedId}
          onClick={() =>
            void run("approve", async () => {
              const pkg = await apiPost<DocumentPackage>(
                `/api/v1/projects/${projectId}/packages/${selectedId}/approve`,
                { decision: "approved" },
                true,
              );
              setNote(`Package approved: ${pkg.title}`);
              await load();
            })
          }
        >
          Approve package
        </button>
        <button
          type="button"
          className="btn-secondary"
          disabled={!!busy || !selectedId}
          onClick={() =>
            void run("export", async () => {
              const result = await apiPost<PackageExport>(
                `/api/v1/projects/${projectId}/packages/${selectedId}/export`,
                {},
                true,
              );
              setExportResult(result);
              setNote(
                result.status === "completed"
                  ? `ZIP ready (checksum ${result.checksum_sha256?.slice(0, 12)}…)`
                  : `Export ${result.status}`,
              );
              await load();
            })
          }
        >
          Export ZIP
        </button>
      </div>

      {packages.length > 0 ? (
        <div style={{ marginTop: 12 }}>
          <label>
            Package{" "}
            <select
              value={selectedId || ""}
              onChange={(e) => setSelectedId(e.target.value || null)}
            >
              {packages.map((pkg) => (
                <option key={pkg.id} value={pkg.id}>
                  {pkg.title} — {pkg.status}
                  {pkg.version_label ? ` v${pkg.version_label}` : ""}
                </option>
              ))}
            </select>
          </label>
        </div>
      ) : (
        <p className="muted" style={{ marginTop: 12 }}>
          No packages yet. Approve the four narrative deliverables and validate
          BOM, then assemble.
        </p>
      )}

      {selected ? (
        <div style={{ marginTop: 12 }}>
          <p className="muted">
            Status <strong>{selected.status}</strong>
            {selected.export_checksum_sha256
              ? ` · ZIP checksum ${selected.export_checksum_sha256.slice(0, 12)}…`
              : null}
            {exportResult?.download_name
              ? ` · Last export ${exportResult.download_name}`
              : null}
          </p>
          <h3>Members</h3>
          <ul>
            {selected.members.map((member) => (
              <li key={member.id}>
                [{member.document_type}] {member.title || member.document_id} —{" "}
                {member.document_status}
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {validation ? (
        <div style={{ marginTop: 8 }}>
          <h3>Package validation</h3>
          <p>{validation.ok ? "OK" : "Issues found"}</p>
          <ul>
            {validation.findings.map((finding, index) => (
              <li key={`${finding.code}-${index}`}>
                [{finding.severity}] {finding.message}
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </section>
  );
}
