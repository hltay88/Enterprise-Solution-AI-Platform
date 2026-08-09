"use client";

import { useEffect, useState } from "react";

import { apiGet, apiPost, ApiClientError } from "@/lib/api";
import type {
  ArchitectureOptionSummary,
  BomImport,
  BomValidationResult,
  VendorCatalogue,
} from "@/lib/types";

type BomValidationPanelProps = {
  projectId: string;
  refreshToken?: number;
};

function parseBomLines(text: string): Array<{
  line_number: number;
  vendor: string;
  product_model: string;
  quantity: number | null;
  category: string;
  description: string;
}> {
  const items: Array<{
    line_number: number;
    vendor: string;
    product_model: string;
    quantity: number | null;
    category: string;
    description: string;
  }> = [];
  const lines = text
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter((line) => line && !line.startsWith("#"));
  lines.forEach((line, index) => {
    const parts = line.split("|").map((part) => part.trim());
    if (parts.length < 2) return;
    const [vendor, product_model, qtyRaw = "", category = "", description = ""] =
      parts;
    let quantity: number | null = null;
    if (qtyRaw) {
      const parsed = Number(qtyRaw);
      quantity = Number.isFinite(parsed) ? parsed : null;
    }
    items.push({
      line_number: index + 1,
      vendor,
      product_model,
      quantity,
      category,
      description: description || product_model,
    });
  });
  return items;
}

export function BomValidationPanel({
  projectId,
  refreshToken = 0,
}: BomValidationPanelProps) {
  const [imports, setImports] = useState<BomImport[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [detail, setDetail] = useState<BomImport | null>(null);
  const [validation, setValidation] = useState<BomValidationResult | null>(null);
  const [architectures, setArchitectures] = useState<ArchitectureOptionSummary[]>(
    [],
  );
  const [source, setSource] = useState("Distributor BOM");
  const [architectureId, setArchitectureId] = useState("");
  const [lines, setLines] = useState(
    "# vendor|product_model|quantity|category|description\nRefNet|RN-AP-6E|24|wireless_ap|Access point",
  );
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [note, setNote] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  async function loadList() {
    const rows = await apiGet<BomImport[]>(
      `/api/v1/projects/${projectId}/bom`,
      true,
    );
    setImports(rows);
    return rows;
  }

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const [rows, options] = await Promise.all([
        loadList(),
        apiGet<ArchitectureOptionSummary[]>(
          `/api/v1/projects/${projectId}/architectures`,
          true,
        ).catch(() => [] as ArchitectureOptionSummary[]),
      ]);
      setArchitectures(options);
      if (rows.length && !selectedId) {
        await selectImport(rows[0].id);
      } else if (selectedId) {
        await selectImport(selectedId);
      } else {
        setDetail(null);
        setValidation(null);
      }
    } catch (err) {
      setError(
        err instanceof ApiClientError
          ? err.message
          : "Unable to load BOM imports",
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId, refreshToken]);

  async function selectImport(bomImportId: string) {
    setSelectedId(bomImportId);
    setError(null);
    try {
      const bom = await apiGet<BomImport>(
        `/api/v1/projects/${projectId}/bom/${bomImportId}`,
        true,
      );
      setDetail(bom);
      try {
        const result = await apiGet<BomValidationResult>(
          `/api/v1/projects/${projectId}/bom/${bomImportId}/validation`,
          true,
        );
        setValidation(result);
      } catch (err) {
        if (err instanceof ApiClientError && err.status === 404) {
          setValidation(null);
        } else {
          throw err;
        }
      }
    } catch (err) {
      setError(
        err instanceof ApiClientError
          ? err.message
          : "Unable to load BOM import",
      );
    }
  }

  async function seedCatalogue() {
    setBusy("seed");
    setError(null);
    setNote(null);
    try {
      const catalogue = await apiPost<VendorCatalogue>(
        "/api/v1/vendors/catalogue/seed",
        {},
        true,
      );
      setNote(
        `Seed catalogue ready: ${catalogue.name} (${catalogue.product_count} products)`,
      );
    } catch (err) {
      setError(
        err instanceof ApiClientError
          ? err.message
          : "Unable to seed vendor catalogue",
      );
    } finally {
      setBusy(null);
    }
  }

  async function importBom() {
    const items = parseBomLines(lines);
    if (!items.length) {
      setError("Add at least one BOM line (vendor|product_model|…)");
      return;
    }
    setBusy("import");
    setError(null);
    setNote(null);
    try {
      const bom = await apiPost<BomImport>(
        `/api/v1/projects/${projectId}/bom/import`,
        {
          source: source.trim() || "Distributor BOM",
          architecture_id: architectureId || null,
          items,
        },
        true,
      );
      setNote(`Imported ${bom.item_count} BOM line(s) as evidence`);
      await loadList();
      await selectImport(bom.id);
    } catch (err) {
      setError(
        err instanceof ApiClientError ? err.message : "Unable to import BOM",
      );
    } finally {
      setBusy(null);
    }
  }

  async function validateBom() {
    if (!selectedId) return;
    setBusy("validate");
    setError(null);
    setNote(null);
    try {
      const result = await apiPost<BomValidationResult>(
        `/api/v1/projects/${projectId}/bom/${selectedId}/validate`,
        {
          architecture_id: architectureId || detail?.architecture_id || null,
        },
        true,
      );
      setValidation(result);
      setNote(result.summary);
    } catch (err) {
      setError(
        err instanceof ApiClientError
          ? err.message
          : "Unable to validate BOM",
      );
    } finally {
      setBusy(null);
    }
  }

  return (
    <section className="panel rkm-panel" id="bom-panel">
      <div className="panel-heading">
        <div>
          <h2>BOM import &amp; validation</h2>
          <p className="muted">
            Phase 3 — external BOMs are evidence (ATLAS-039). Seed the vendor
            catalogue, import lines, then validate against architecture.
          </p>
        </div>
        <button
          className="btn-secondary btn-compact"
          type="button"
          disabled={busy != null}
          onClick={() => void seedCatalogue()}
        >
          {busy === "seed" ? "Seeding…" : "Seed catalogue"}
        </button>
      </div>

      {error ? <p className="form-error">{error}</p> : null}
      {note ? <p className="status">{note}</p> : null}
      {loading ? <p className="status">Loading…</p> : null}

      <div className="rkm-section">
        <h3>Import distributor BOM</h3>
        <label className="field">
          <span>Source</span>
          <input
            value={source}
            onChange={(event) => setSource(event.target.value)}
          />
        </label>
        <label className="field">
          <span>Link architecture (optional)</span>
          <select
            value={architectureId}
            onChange={(event) => setArchitectureId(event.target.value)}
          >
            <option value="">— none —</option>
            {architectures.map((item) => (
              <option key={item.id} value={item.id}>
                {item.title} ({item.candidate_key}) · {item.status}
              </option>
            ))}
          </select>
        </label>
        <label className="field">
          <span>Lines (vendor|model|qty|category|description)</span>
          <textarea
            rows={5}
            value={lines}
            onChange={(event) => setLines(event.target.value)}
          />
        </label>
        <button
          className="btn-primary btn-compact"
          type="button"
          disabled={busy != null}
          onClick={() => void importBom()}
        >
          {busy === "import" ? "Importing…" : "Import BOM"}
        </button>
      </div>

      <div className="rkm-section">
        <h3>Imported evidence</h3>
        {imports.length === 0 ? (
          <p className="muted">No BOM imports yet.</p>
        ) : (
          <ul className="rkm-list">
            {imports.map((item) => (
              <li key={item.id} className="rkm-item">
                <button
                  type="button"
                  className={
                    item.id === selectedId
                      ? "architecture-candidate-btn is-active"
                      : "architecture-candidate-btn"
                  }
                  onClick={() => void selectImport(item.id)}
                >
                  <span className="rkm-item-head">
                    <strong>{item.source}</strong>
                    <span className="muted">
                      {item.item_count} lines ·{" "}
                      {new Date(item.created_at).toLocaleString()}
                    </span>
                  </span>
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      {detail ? (
        <div className="rkm-section">
          <div className="panel-heading">
            <h3>Lines</h3>
            <button
              className="btn-primary btn-compact"
              type="button"
              disabled={busy != null}
              onClick={() => void validateBom()}
            >
              {busy === "validate" ? "Validating…" : "Validate BOM"}
            </button>
          </div>
          <ul className="rkm-list">
            {detail.items.map((item) => (
              <li key={item.id} className="rkm-item">
                <div className="rkm-item-head">
                  <strong>
                    #{item.line_number} {item.vendor} {item.product_model}
                  </strong>
                  <span className="muted">
                    qty {item.quantity ?? "—"}
                    {item.mapped_product_id ? " · linked" : " · unmapped"}
                  </span>
                </div>
                {item.description ? (
                  <p className="muted">{item.description}</p>
                ) : null}
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {validation ? (
        <div className="rkm-section">
          <h3>Validation · {validation.status.replace(/_/g, " ")}</h3>
          <p>{validation.summary}</p>
          {validation.issues.length === 0 ? (
            <p className="muted">No issues recorded.</p>
          ) : (
            <ul className="rkm-list">
              {validation.issues.map((issue, index) => (
                <li
                  key={`${issue.code}-${issue.line_number ?? "x"}-${index}`}
                  className="rkm-item"
                >
                  <div className="rkm-item-head">
                    <strong>
                      {issue.code.replace(/_/g, " ")} · {issue.severity}
                    </strong>
                    <span className="muted">
                      {issue.line_number != null
                        ? `line ${issue.line_number}`
                        : "import"}
                      {issue.requires_human_validation ? " · human review" : ""}
                    </span>
                  </div>
                  <p className="muted">{issue.message}</p>
                </li>
              ))}
            </ul>
          )}
        </div>
      ) : null}
    </section>
  );
}
