"""Phase 3 vendor seed catalogue loader (Sprint 3.3 Task 4).

Loads the frozen vendor-neutral fixture from
``knowledge/phase3/vendors/seed_catalogue.json``. Does not invent SKUs beyond
the committed seed file (ATLAS-035/038).
"""

from __future__ import annotations

import json
from datetime import date, datetime
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.schemas.vendor_bom import VendorCatalogueImportIn
from app.services.phase3_domain_catalog import phase3_root

SEED_CATALOGUE_NAME = "Atlas seed catalogue"
SEED_SOURCE = "Approved internal catalogue (Atlas seed)"


class VendorSeedError(ValueError):
    """Raised when the Phase 3 vendor seed pack is missing or invalid."""


def vendors_root() -> Path:
    return phase3_root() / "vendors"


def seed_catalogue_path() -> Path:
    return vendors_root() / "seed_catalogue.json"


def clear_vendor_seed_cache() -> None:
    """Test helper — drop cached seed reads."""
    load_seed_catalogue_payload.cache_clear()


def _parse_date(value: Any) -> date | None:
    if value is None or value == "":
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    text = str(value).strip()
    if not text:
        return None
    return date.fromisoformat(text)


@lru_cache(maxsize=1)
def load_seed_catalogue_payload() -> dict[str, Any]:
    path = seed_catalogue_path()
    if not path.is_file():
        raise VendorSeedError(f"Vendor seed catalogue missing: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise VendorSeedError(f"Vendor seed catalogue is not valid JSON: {path}") from exc
    if not isinstance(payload, dict):
        raise VendorSeedError("Vendor seed catalogue root must be an object")
    products = payload.get("products")
    if not isinstance(products, list) or not products:
        raise VendorSeedError("Vendor seed catalogue must include a non-empty products list")
    for index, item in enumerate(products):
        if not isinstance(item, dict):
            raise VendorSeedError(f"products[{index}] must be an object")
        vendor = str(item.get("vendor") or "").strip()
        model = str(item.get("product_model") or "").strip()
        source = str(item.get("source") or "").strip()
        if not vendor or not model or not source:
            raise VendorSeedError(
                f"products[{index}] requires vendor, product_model, and source",
            )
        # Guard against accidental real-vendor lock-in in the seed pack.
        banned = {"cisco", "aruba", "hpe", "dell", "huawei", "juniper", "fortinet"}
        if vendor.lower() in banned:
            raise VendorSeedError(
                f"seed product vendor '{vendor}' looks like a real OEM; "
                "use fictional reference vendors only (ATLAS-035)",
            )
    return payload


def seed_version() -> str:
    payload = load_seed_catalogue_payload()
    return str(payload.get("seed_version") or "1.0.0").strip() or "1.0.0"


def build_seed_catalogue_import() -> VendorCatalogueImportIn:
    """Return a validated import DTO from the frozen seed file."""
    payload = load_seed_catalogue_payload()
    body = {
        "name": str(payload.get("name") or SEED_CATALOGUE_NAME).strip() or SEED_CATALOGUE_NAME,
        "source": str(payload.get("source") or SEED_SOURCE).strip() or SEED_SOURCE,
        "source_date": _parse_date(payload.get("source_date")),
        "version_label": str(payload.get("version_label") or seed_version()).strip()
        or "1.0.0",
        "region": (str(payload.get("region")).strip() if payload.get("region") else None)
        or None,
        "notes": (str(payload.get("notes")).strip() if payload.get("notes") else None)
        or None,
        "products": payload.get("products") or [],
    }
    try:
        return VendorCatalogueImportIn.model_validate(body)
    except Exception as exc:  # pydantic ValidationError
        raise VendorSeedError(f"Vendor seed catalogue failed validation: {exc}") from exc
