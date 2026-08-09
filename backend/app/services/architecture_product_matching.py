"""Sprint 3.3 Task 5 — capability→product matching helpers (no DB/HTTP).

Maps architecture component text to catalogue products using capability codes
and categories only. Does not invent SKUs or prefer a vendor by name in the
customer ask (ATLAS-035).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


# Component text cues → catalogue capability codes / categories (seed-aligned).
_COMPONENT_CUES: tuple[tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]], ...] = (
    (("wifi", "wi-fi", "wlan", "access point", " ap ", "wireless"), ("wifi6e", "seamless_roaming"), ("wireless_ap",)),
    (("wlan controller", "wireless controller", "cloud wlan", "wlan mgmt"), ("cloud_wlan_mgmt",), ("wlan_management",)),
    (("access switch", "poe", "switching", "access layer"), ("poe_plus", "1g_access"), ("access_switch",)),
    (("firewall", "ngfw", "ips"), ("ngfw", "ips"), ("firewall",)),
    (("ztna", "zero trust", "secure access", "vpn gateway"), ("ztna", "mfa_integration"), ("ztna",)),
    (("nac", "802.1x", "radius", "guest portal"), ("8021x", "guest_portal"), ("nac",)),
    (("monitoring", "observability", "nms", "alerting"), ("network_monitoring", "alerting"), ("monitoring",)),
    (("leaf", "spine", "data centre", "data center", "fabric"), ("leaf_spine", "25g_50g"), ("leaf_switch",)),
    (("sd-wan", "sdwan", "wan edge", "hybrid cloud"), ("sdwan", "hybrid_cloud"), ("sdwan_edge",)),
)


@dataclass(frozen=True, slots=True)
class ProductMatchCandidate:
    product_id: str
    fit_score: float
    rationale: str
    limitations: str
    preference_kind: str = "technical"


def infer_component_needs(component: dict[str, Any]) -> tuple[set[str], set[str]]:
    """Return (capability_codes, categories) inferred from component fields."""
    blob = " ".join(
        [
            str(component.get("name") or ""),
            str(component.get("purpose") or ""),
            str(component.get("component_kind") or ""),
        ],
    ).lower()
    # Pad short tokens so "ap" cue can match word boundaries loosely.
    padded = f" {blob} "
    caps: set[str] = set()
    cats: set[str] = set()
    for cues, capability_codes, categories in _COMPONENT_CUES:
        if any(cue in padded or cue in blob for cue in cues):
            caps.update(capability_codes)
            cats.update(categories)
    return caps, cats


def score_product_for_component(
    *,
    needed_capabilities: set[str],
    needed_categories: set[str],
    product: dict[str, Any],
    region: str | None = None,
) -> ProductMatchCandidate | None:
    """Score one catalogue product. Returns None when clearly unrelated."""
    product_id = str(product.get("id") or "").strip()
    if not product_id:
        return None

    product_caps = {
        str(item.get("capability_code") or "").strip().lower()
        for item in (product.get("capabilities") or [])
        if isinstance(item, dict)
    }
    product_caps.discard("")
    category = str(product.get("category") or "").strip().lower()

    if not needed_capabilities and not needed_categories:
        return None

    cap_hits = len(needed_capabilities & product_caps)
    cat_hit = 1.0 if category and category in needed_categories else 0.0
    if cap_hits == 0 and cat_hit == 0.0:
        return None

    cap_ratio = (
        cap_hits / len(needed_capabilities) if needed_capabilities else (1.0 if cat_hit else 0.0)
    )
    # Fit on 0–5 scale: capability match dominates, category supports.
    fit = round(min(5.0, (cap_ratio * 3.5) + (cat_hit * 1.0) + min(0.5, cap_hits * 0.25)), 2)

    limitations: list[str] = []
    lifecycle = str(product.get("lifecycle_status") or "unknown").lower()
    if lifecycle in {"end_of_sale", "end_of_support", "discontinued"}:
        fit = max(0.0, fit - 1.5)
        limitations.append(f"lifecycle_status={lifecycle}")
    if product.get("is_stale"):
        fit = max(0.0, fit - 0.75)
        limitations.append("catalogue data may be stale (ATLAS-038)")

    product_region = str(product.get("region") or "").strip()
    if region and product_region and product_region.lower() != region.strip().lower():
        fit = max(0.0, fit - 0.5)
        limitations.append(
            f"regional availability ({product_region}) differs from requested ({region})",
        )

    if fit < 1.5:
        return None

    vendor = str(product.get("vendor") or "").strip()
    model = str(product.get("product_model") or "").strip()
    rationale = (
        f"Technical fit via capabilities {sorted(needed_capabilities & product_caps) or '[]'} "
        f"and category '{category or 'n/a'}' → {vendor} {model}".strip()
    )
    return ProductMatchCandidate(
        product_id=product_id,
        fit_score=fit,
        rationale=rationale,
        limitations="; ".join(limitations),
        preference_kind="technical",
    )


def rank_products_for_component(
    *,
    component: dict[str, Any],
    products: list[dict[str, Any]],
    region: str | None = None,
    limit: int = 3,
) -> list[ProductMatchCandidate]:
    """Return top product candidates for one component (best fit first)."""
    needed_caps, needed_cats = infer_component_needs(component)
    scored: list[ProductMatchCandidate] = []
    for product in products:
        if not isinstance(product, dict):
            continue
        candidate = score_product_for_component(
            needed_capabilities=needed_caps,
            needed_categories=needed_cats,
            product=product,
            region=region,
        )
        if candidate is not None:
            scored.append(candidate)
    scored.sort(key=lambda item: item.fit_score, reverse=True)
    return scored[: max(1, limit)]
