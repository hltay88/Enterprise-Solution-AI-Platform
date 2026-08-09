"""BOM validation heuristics (Sprint 3.3 Task 8, ATLAS-039).

Pure functions — no DB/HTTP. Flags uncertainty for human review; never treats
imported distributor lines as unquestioned truth.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from app.services.architecture_product_matching import infer_component_needs

# Categories / keywords that often need companion lines (flag, don't invent).
_SUPPORT_KEYWORDS = ("support", "smc", "smartnet", "care", "warranty")
_LICENCE_KEYWORDS = ("licence", "license", "entitlement", "subscription")
_OPTICS_KEYWORDS = ("optic", "sfp", "transceiver", "qsfp")
_POWER_KEYWORDS = ("power supply", "psu", "redundant power")
_ACCESSORY_KEYWORDS = ("accessory", "mounting", "rail kit", "antenna")


@dataclass(slots=True)
class BomIssue:
    code: str
    severity: str
    message: str
    bom_item_id: UUID | None = None
    line_number: int | None = None
    related_component_id: UUID | None = None
    requires_human_validation: bool = True


@dataclass(slots=True)
class BomValidationOutcome:
    status: str
    summary: str
    issues: list[BomIssue] = field(default_factory=list)


def _item_key(item: dict[str, Any]) -> str:
    vendor = str(item.get("vendor") or "").strip().lower()
    model = str(item.get("product_model") or "").strip().lower()
    sku = str(item.get("sku") or "").strip().lower()
    if vendor and model:
        return f"{vendor}|{model}"
    if sku:
        return f"sku|{sku}"
    if model:
        return f"model|{model}"
    return f"desc|{str(item.get('description') or '').strip().lower()}"


def _item_categories(item: dict[str, Any], product: dict[str, Any] | None) -> set[str]:
    cats: set[str] = set()
    raw = str(item.get("category") or "").strip().lower()
    if raw:
        cats.add(raw)
    if product:
        pcat = str(product.get("category") or "").strip().lower()
        if pcat:
            cats.add(pcat)
    blob = " ".join(
        [
            str(item.get("vendor") or ""),
            str(item.get("product_model") or ""),
            str(item.get("description") or ""),
            str(item.get("category") or ""),
        ],
    )
    _, inferred = infer_component_needs(
        {"name": blob, "purpose": "", "component_kind": ""},
    )
    cats.update(inferred)
    return cats


def _blob(item: dict[str, Any]) -> str:
    return " ".join(
        [
            str(item.get("vendor") or ""),
            str(item.get("product_model") or ""),
            str(item.get("description") or ""),
            str(item.get("category") or ""),
            str(item.get("notes") or ""),
        ],
    ).lower()


def _has_keyword(items: list[dict[str, Any]], keywords: tuple[str, ...]) -> bool:
    for item in items:
        text = _blob(item)
        if any(word in text for word in keywords):
            return True
    return False


def derive_validation_status(issues: list[BomIssue]) -> str:
    if any(issue.severity in {"error", "critical"} for issue in issues):
        return "failed"
    if not issues:
        return "passed"
    if any(
        issue.severity == "warning" or issue.requires_human_validation for issue in issues
    ):
        return "needs_review"
    return "passed"


def validate_bom_items(
    *,
    items: list[dict[str, Any]],
    products_by_id: dict[UUID, dict[str, Any]] | None = None,
    components: list[dict[str, Any]] | None = None,
) -> BomValidationOutcome:
    """Compare BOM lines to catalogue + optional architecture components."""
    products_by_id = products_by_id or {}
    components = components or []
    issues: list[BomIssue] = []

    if not items:
        issues.append(
            BomIssue(
                code="other",
                severity="error",
                message="BOM import has no line items to validate",
                requires_human_validation=True,
            ),
        )
        return BomValidationOutcome(
            status="failed",
            summary="Validation failed: empty BOM",
            issues=issues,
        )

    # --- Per-line checks -------------------------------------------------------
    key_to_items: dict[str, list[dict[str, Any]]] = defaultdict(list)
    covered_categories: set[str] = set()

    for item in items:
        item_id = item.get("id")
        bom_item_id = UUID(str(item_id)) if item_id else None
        line = item.get("line_number")
        try:
            line_number = int(line) if line is not None else None
        except (TypeError, ValueError):
            line_number = None

        key_to_items[_item_key(item)].append(item)

        qty = item.get("quantity")
        if qty is None:
            issues.append(
                BomIssue(
                    code="missing_quantity",
                    severity="warning",
                    message="Quantity missing — confirm before procurement (ATLAS-039)",
                    bom_item_id=bom_item_id,
                    line_number=line_number,
                ),
            )

        mapped = item.get("mapped_product_id")
        product: dict[str, Any] | None = None
        if mapped:
            product = products_by_id.get(UUID(str(mapped)))

        model = str(item.get("product_model") or "").strip()
        sku = str(item.get("sku") or "").strip()
        if not product and (model or sku):
            issues.append(
                BomIssue(
                    code="unknown_model",
                    severity="warning",
                    message=(
                        f"Model/SKU not found in catalogue"
                        f"{f' ({model or sku})' if (model or sku) else ''} — "
                        "human validation required"
                    ),
                    bom_item_id=bom_item_id,
                    line_number=line_number,
                ),
            )
        elif product:
            lifecycle = str(product.get("lifecycle_status") or "").lower()
            if lifecycle in {"end_of_sale", "end_of_support", "discontinued"}:
                issues.append(
                    BomIssue(
                        code="compatibility",
                        severity="error",
                        message=(
                            f"Catalogue product has lifecycle_status={lifecycle} — "
                            "not suitable without exception"
                        ),
                        bom_item_id=bom_item_id,
                        line_number=line_number,
                        requires_human_validation=True,
                    ),
                )
            if product.get("is_stale"):
                issues.append(
                    BomIssue(
                        code="stale_catalogue",
                        severity="warning",
                        message="Linked catalogue entry is stale (source > 365 days)",
                        bom_item_id=bom_item_id,
                        line_number=line_number,
                    ),
                )
            specs = product.get("specifications")
            confidence = product.get("confidence")
            if specs in (None, {}, []) or (
                confidence is not None and float(confidence) < 0.5
            ):
                issues.append(
                    BomIssue(
                        code="uncertain_spec",
                        severity="warning",
                        message="Product specifications uncertain — do not treat as fact",
                        bom_item_id=bom_item_id,
                        line_number=line_number,
                    ),
                )

        covered_categories |= _item_categories(item, product)

    # --- Duplicates ------------------------------------------------------------
    for key, group in key_to_items.items():
        if len(group) < 2 or key.startswith("desc|"):
            continue
        lines = sorted(
            {
                int(i["line_number"])
                for i in group
                if i.get("line_number") is not None
            },
        )
        first = group[0]
        issues.append(
            BomIssue(
                code="duplicate_component",
                severity="warning",
                message=(
                    f"Duplicate BOM lines for the same model/SKU"
                    f"{f' (lines {lines})' if lines else ''} — confirm intentional"
                ),
                bom_item_id=UUID(str(first["id"])) if first.get("id") else None,
                line_number=int(first["line_number"])
                if first.get("line_number") is not None
                else None,
            ),
        )

    # --- Architecture coverage (missing components) ----------------------------
    for component in components:
        needed_caps, needed_cats = infer_component_needs(component)
        if not needed_caps and not needed_cats:
            continue
        if needed_cats & covered_categories:
            continue
        # Soft text overlap on BOM blobs as fallback.
        name = str(component.get("name") or "").strip()
        covered_by_text = any(
            token and token in _blob(item)
            for item in items
            for token in name.lower().split()
            if len(token) >= 4
        )
        if covered_by_text:
            continue
        comp_id = component.get("id")
        issues.append(
            BomIssue(
                code="missing_component",
                severity="error",
                message=(
                    f"Architecture component '{name or 'unnamed'}' has no matching "
                    "BOM coverage — confirm gap or update BOM"
                ),
                related_component_id=UUID(str(comp_id)) if comp_id else None,
                requires_human_validation=True,
            ),
        )

    # --- Companion / dependency style flags (keyword heuristics) ---------------
    has_switchish = bool(
        covered_categories
        & {"access_switch", "leaf_switch", "wireless_ap", "firewall", "sdwan_edge"},
    )
    if has_switchish and not _has_keyword(items, _SUPPORT_KEYWORDS):
        issues.append(
            BomIssue(
                code="support",
                severity="info",
                message="No support/care SKU detected — confirm support entitlement",
                requires_human_validation=False,
            ),
        )
    if has_switchish and not _has_keyword(items, _LICENCE_KEYWORDS):
        # Only flag when architecture or categories suggest licensed features.
        if any(
            cat in covered_categories
            for cat in {"firewall", "ztna", "nac", "wlan_management", "sdwan_edge"}
        ):
            issues.append(
                BomIssue(
                    code="licence",
                    severity="warning",
                    message=(
                        "Licensed/subscription features likely required for mapped "
                        "categories — confirm licence/subscription lines"
                    ),
                ),
            )
            issues.append(
                BomIssue(
                    code="subscription",
                    severity="info",
                    message="Confirm recurring subscription coverage if applicable",
                    requires_human_validation=False,
                ),
            )
    if "leaf_switch" in covered_categories and not _has_keyword(items, _OPTICS_KEYWORDS):
        issues.append(
            BomIssue(
                code="optics",
                severity="warning",
                message="Leaf/fabric gear present without optics/transceiver lines",
            ),
        )
    if (
        covered_categories & {"access_switch", "leaf_switch", "firewall"}
        and not _has_keyword(items, _POWER_KEYWORDS)
    ):
        issues.append(
            BomIssue(
                code="power",
                severity="info",
                message="Confirm redundant PSU / power accessories if required",
                requires_human_validation=False,
            ),
        )
    if "wireless_ap" in covered_categories and not _has_keyword(items, _ACCESSORY_KEYWORDS):
        issues.append(
            BomIssue(
                code="accessory",
                severity="info",
                message="Confirm mounting kits / antennas for wireless APs",
                requires_human_validation=False,
            ),
        )

    # Dependency: APs without PoE/access switching when architecture expects both.
    arch_cats: set[str] = set()
    for component in components:
        _, cats = infer_component_needs(component)
        arch_cats |= cats
    if (
        "wireless_ap" in covered_categories
        and "access_switch" in arch_cats
        and "access_switch" not in covered_categories
    ):
        issues.append(
            BomIssue(
                code="dependency",
                severity="warning",
                message=(
                    "Wireless APs present but architecture expects access switching / "
                    "PoE — confirm dependency coverage"
                ),
            ),
        )

    status = derive_validation_status(issues)
    error_n = sum(1 for i in issues if i.severity in {"error", "critical"})
    warn_n = sum(1 for i in issues if i.severity == "warning")
    human_n = sum(1 for i in issues if i.requires_human_validation)
    if status == "passed":
        summary = f"BOM validation passed ({len(items)} lines, {len(issues)} info notes)"
    elif status == "failed":
        summary = (
            f"BOM validation failed: {error_n} error(s), {warn_n} warning(s); "
            f"{human_n} item(s) need human review (ATLAS-039)"
        )
    else:
        summary = (
            f"BOM needs review: {warn_n} warning(s), {human_n} human flag(s) "
            f"across {len(items)} lines (ATLAS-039)"
        )

    return BomValidationOutcome(status=status, summary=summary, issues=issues)
