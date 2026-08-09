"""Pure helpers for vendor analytics aggregations (Phase 3 P2).

No DB/HTTP. Never invents commercial or SKU facts — only aggregates provided rows.
"""

from __future__ import annotations

from collections import Counter
from typing import Any


def _count_field(rows: list[dict[str, Any]], field: str, *, default: str = "unknown") -> list[dict[str, Any]]:
    counter: Counter[str] = Counter()
    for row in rows:
        key = str(row.get(field) or "").strip() or default
        counter[key] += 1
    return [{"key": key, "count": count} for key, count in sorted(counter.items())]


def catalogue_analytics_from_products(
    products: list[dict[str, Any]],
    *,
    catalogue_id: str | None = None,
    catalogue_name: str | None = None,
) -> dict[str, Any]:
    total = len(products)
    stale = sum(1 for item in products if item.get("is_stale"))
    confidences = [
        float(item["confidence"])
        for item in products
        if item.get("confidence") is not None
    ]
    avg_conf = round(sum(confidences) / len(confidences), 4) if confidences else None
    warnings: list[str] = []
    if total and stale / total >= 0.25:
        warnings.append(
            f"{stale}/{total} products are stale (source_date > 365 days) — ATLAS-038",
        )
    lifecycle = _count_field(products, "lifecycle_status")
    if any(
        item["key"] in {"end_of_sale", "end_of_support", "discontinued"}
        and item["count"] > 0
        for item in lifecycle
    ):
        warnings.append(
            "Catalogue includes end-of-sale/support or discontinued products",
        )
    return {
        "catalogue_id": catalogue_id,
        "catalogue_name": catalogue_name,
        "product_count": total,
        "stale_count": stale,
        "stale_ratio": round(stale / total, 4) if total else 0.0,
        "average_confidence": avg_conf,
        "by_vendor": _count_field(products, "vendor", default="(unknown vendor)"),
        "by_category": _count_field(products, "category", default="(uncategorized)"),
        "by_lifecycle": lifecycle,
        "by_region": _count_field(products, "region", default="(unspecified)"),
        "warnings": warnings,
    }


def mapping_analytics_from_rows(
    mappings: list[dict[str, Any]],
    products_by_id: dict[str, dict[str, Any]],
    *,
    project_id: str,
    architecture_id: str | None = None,
    component_ids: list[str] | None = None,
) -> dict[str, Any]:
    enriched: list[dict[str, Any]] = []
    fit_scores: list[float] = []
    stale_mapped = 0
    mapped_components: set[str] = set()
    for row in mappings:
        product_id = str(row.get("product_id") or "")
        product = products_by_id.get(product_id) or {}
        vendor = product.get("vendor") or row.get("vendor") or ""
        lifecycle = product.get("lifecycle_status") or "unknown"
        if product.get("is_stale"):
            stale_mapped += 1
        component_id = str(row.get("component_id") or "").strip()
        if component_id:
            mapped_components.add(component_id)
        if row.get("fit_score") is not None:
            try:
                score = float(row["fit_score"])
                # Defensive: if someone stored 0–100, normalize to 0–5.
                if score > 5.0:
                    score = score / 20.0
                fit_scores.append(score)
            except (TypeError, ValueError):
                pass
        enriched.append(
            {
                "status": row.get("status") or "candidate",
                "preference_kind": row.get("preference_kind") or "technical",
                "vendor": vendor,
                "lifecycle_status": lifecycle,
            },
        )

    by_status = _count_field(enriched, "status")
    status_map = {item["key"]: item["count"] for item in by_status}
    warnings: list[str] = []
    if stale_mapped:
        warnings.append(
            f"{stale_mapped} mapped product(s) use stale catalogue data (ATLAS-038)",
        )
    if any(
        item["key"] in {"end_of_sale", "end_of_support", "discontinued"}
        and item["count"] > 0
        for item in _count_field(enriched, "lifecycle_status")
    ):
        warnings.append(
            "Mapped products include end-of-lifecycle SKUs — confirm before selection",
        )
    if status_map.get("selected", 0) == 0 and mappings:
        warnings.append("No products marked selected yet — mapping is still candidates-only")

    known_components = {str(cid).strip() for cid in (component_ids or []) if str(cid).strip()}
    component_count = len(known_components) if known_components else None
    mapped_component_count = (
        len(known_components & mapped_components)
        if known_components
        else len(mapped_components)
    )
    unmatched = sorted(known_components - mapped_components) if known_components else []
    unmatched_count = len(unmatched)
    coverage_ratio = (
        round(mapped_component_count / component_count, 4)
        if component_count
        else None
    )
    if unmatched_count:
        warnings.append(
            f"{unmatched_count} architecture component(s) have no product mapping",
        )

    return {
        "project_id": project_id,
        "architecture_id": architecture_id,
        "mapping_count": len(mappings),
        "by_status": by_status,
        "by_preference_kind": _count_field(enriched, "preference_kind"),
        "by_vendor": _count_field(enriched, "vendor", default="(unknown vendor)"),
        "by_lifecycle": _count_field(enriched, "lifecycle_status"),
        "fit_score_buckets": _fit_score_buckets(fit_scores),
        "component_count": component_count if component_count is not None else 0,
        "mapped_component_count": mapped_component_count,
        "unmatched_component_count": unmatched_count,
        "unmatched_component_ids": unmatched[:50],
        "coverage_ratio": coverage_ratio if coverage_ratio is not None else 0.0,
        "stale_mapped_count": stale_mapped,
        "average_fit_score": (
            round(sum(fit_scores) / len(fit_scores), 2) if fit_scores else None
        ),
        "selected_count": int(status_map.get("selected", 0)),
        "candidate_count": int(status_map.get("candidate", 0)),
        "rejected_count": int(status_map.get("rejected", 0)),
        "warnings": warnings,
    }


def _fit_score_buckets(scores: list[float]) -> list[dict[str, Any]]:
    """Bucket fit scores on the 0–5 matching scale."""
    labels = ("0–1.5", "1.5–3", "3–4", "4–5")
    counts = [0, 0, 0, 0]
    for score in scores:
        if score < 1.5:
            counts[0] += 1
        elif score < 3.0:
            counts[1] += 1
        elif score < 4.0:
            counts[2] += 1
        else:
            counts[3] += 1
    return [{"key": label, "count": count} for label, count in zip(labels, counts)]
