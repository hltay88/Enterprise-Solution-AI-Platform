"""Persistence for vendor catalogues and products (Sprint 3.3 Task 3).

Data access only — no AI, no HTTP. Never invents SKU specifications.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.vendor_bom import ProductCapability, VendorCatalogue, VendorProduct


class VendorCatalogueRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_catalogue(self, catalogue_id: UUID) -> VendorCatalogue | None:
        return self.db.scalars(
            select(VendorCatalogue).where(VendorCatalogue.id == catalogue_id),
        ).first()

    def get_by_name_and_source(
        self,
        *,
        name: str,
        source: str,
    ) -> VendorCatalogue | None:
        """Latest catalogue matching name + source (used for seed idempotency)."""
        statement = (
            select(VendorCatalogue)
            .where(
                VendorCatalogue.name == name,
                VendorCatalogue.source == source,
            )
            .order_by(VendorCatalogue.created_at.desc())
        )
        return self.db.scalars(statement).first()

    def list_catalogues(self, *, limit: int = 50) -> list[VendorCatalogue]:
        statement = (
            select(VendorCatalogue)
            .order_by(VendorCatalogue.created_at.desc())
            .limit(max(1, min(limit, 200)))
        )
        return list(self.db.scalars(statement).all())

    def count_products(self, catalogue_id: UUID) -> int:
        statement = (
            select(func.count())
            .select_from(VendorProduct)
            .where(VendorProduct.catalogue_id == catalogue_id)
        )
        return int(self.db.scalar(statement) or 0)

    def list_products(
        self,
        catalogue_id: UUID,
        *,
        include_stale: bool = True,
    ) -> list[VendorProduct]:
        statement = select(VendorProduct).where(
            VendorProduct.catalogue_id == catalogue_id,
        )
        if not include_stale:
            statement = statement.where(VendorProduct.is_stale.is_(False))
        statement = statement.order_by(
            VendorProduct.vendor.asc(),
            VendorProduct.product_model.asc(),
        )
        return list(self.db.scalars(statement).all())

    def list_capabilities(self, product_id: UUID) -> list[ProductCapability]:
        statement = (
            select(ProductCapability)
            .where(ProductCapability.product_id == product_id)
            .order_by(ProductCapability.capability_code.asc())
        )
        return list(self.db.scalars(statement).all())

    def get_product(self, product_id: UUID) -> VendorProduct | None:
        return self.db.scalars(
            select(VendorProduct).where(VendorProduct.id == product_id),
        ).first()

    def search_products(
        self,
        *,
        query: str = "",
        vendor: str | None = None,
        category: str | None = None,
        region: str | None = None,
        catalogue_id: UUID | None = None,
        include_stale: bool = False,
        limit: int = 50,
    ) -> list[VendorProduct]:
        statement = select(VendorProduct)
        if catalogue_id is not None:
            statement = statement.where(VendorProduct.catalogue_id == catalogue_id)
        if not include_stale:
            statement = statement.where(VendorProduct.is_stale.is_(False))
        if vendor:
            statement = statement.where(
                func.lower(VendorProduct.vendor) == vendor.strip().lower(),
            )
        if category:
            statement = statement.where(
                func.lower(VendorProduct.category) == category.strip().lower(),
            )
        if region:
            statement = statement.where(
                func.lower(VendorProduct.region) == region.strip().lower(),
            )
        text = (query or "").strip()
        if text:
            pattern = f"%{text.lower()}%"
            statement = statement.where(
                or_(
                    func.lower(VendorProduct.vendor).like(pattern),
                    func.lower(VendorProduct.product_model).like(pattern),
                    func.lower(VendorProduct.product_family).like(pattern),
                    func.lower(VendorProduct.category).like(pattern),
                ),
            )
        statement = statement.order_by(
            VendorProduct.vendor.asc(),
            VendorProduct.product_model.asc(),
        ).limit(max(1, min(limit, 200)))
        return list(self.db.scalars(statement).all())

    def create_catalogue_tree(
        self,
        *,
        name: str,
        source: str,
        source_date: date | None,
        version_label: str,
        region: str | None,
        notes: str | None,
        imported_by: UUID | None,
        products: list[dict[str, Any]],
        payload_json: dict[str, Any] | None = None,
        commit: bool = True,
    ) -> VendorCatalogue:
        """Persist a catalogue import with products and capabilities.

        ``products`` items are dicts matching VendorProductIn fields
        (capabilities nested). Does not invent specifications.
        """
        if not products:
            raise ValueError("at least one product is required")
        source_text = str(source or "").strip()
        if not source_text:
            raise ValueError("catalogue source is required")

        now = datetime.now(timezone.utc)
        catalogue = VendorCatalogue(
            id=uuid4(),
            name=str(name or "").strip(),
            source=source_text,
            source_date=source_date,
            version_label=str(version_label or "1.0.0").strip() or "1.0.0",
            region=(str(region).strip() if region else None) or None,
            notes=(str(notes).strip() if notes else None) or None,
            imported_by=imported_by,
            payload_json=dict(payload_json or {}),
            created_at=now,
        )
        self.db.add(catalogue)
        self.db.flush()

        seen_keys: set[tuple[str, str]] = set()
        for index, item in enumerate(products):
            if not isinstance(item, dict):
                raise ValueError(f"products[{index}] must be an object")
            vendor = str(item.get("vendor") or "").strip()
            product_model = str(item.get("product_model") or "").strip()
            product_source = str(item.get("source") or source_text).strip()
            if not vendor:
                raise ValueError(f"products[{index}].vendor is required")
            if not product_model:
                raise ValueError(f"products[{index}].product_model is required")
            if not product_source:
                raise ValueError(f"products[{index}].source is required")
            key = (vendor.lower(), product_model.lower())
            if key in seen_keys:
                raise ValueError(
                    f"duplicate vendor/product_model in import: {vendor} / {product_model}",
                )
            seen_keys.add(key)

            specs = item.get("specifications") or {}
            if specs is not None and not isinstance(specs, dict):
                raise ValueError(f"products[{index}].specifications must be an object")

            product = VendorProduct(
                id=uuid4(),
                catalogue_id=catalogue.id,
                vendor=vendor,
                product_family=str(item.get("product_family") or "").strip(),
                product_model=product_model,
                category=str(item.get("category") or "").strip(),
                specifications=dict(specs or {}),
                licensing=(
                    str(item.get("licensing")).strip()
                    if item.get("licensing")
                    else None
                )
                or None,
                lifecycle_status=str(item.get("lifecycle_status") or "unknown").strip()
                or "unknown",
                source=product_source,
                source_date=item.get("source_date") or source_date,
                region=(
                    str(item.get("region")).strip()
                    if item.get("region")
                    else (str(region).strip() if region else None)
                )
                or None,
                confidence=float(item.get("confidence") or 0.0),
                is_stale=bool(item.get("is_stale") or False),
                created_at=now,
                updated_at=now,
            )
            self.db.add(product)
            self.db.flush()

            caps = item.get("capabilities") or []
            if not isinstance(caps, list):
                raise ValueError(f"products[{index}].capabilities must be a list")
            seen_codes: set[str] = set()
            for cap_index, cap in enumerate(caps):
                if not isinstance(cap, dict):
                    raise ValueError(
                        f"products[{index}].capabilities[{cap_index}] must be an object",
                    )
                code = str(cap.get("capability_code") or "").strip().lower().replace(
                    " ",
                    "_",
                )
                if not code:
                    raise ValueError(
                        f"products[{index}].capabilities[{cap_index}].capability_code "
                        "is required",
                    )
                if code in seen_codes:
                    raise ValueError(
                        f"duplicate capability_code on product {product_model}: {code}",
                    )
                seen_codes.add(code)
                details = cap.get("details") or {}
                if details is not None and not isinstance(details, dict):
                    raise ValueError(
                        f"products[{index}].capabilities[{cap_index}].details "
                        "must be an object",
                    )
                self.db.add(
                    ProductCapability(
                        id=uuid4(),
                        product_id=product.id,
                        capability_code=code,
                        capability_label=str(cap.get("capability_label") or "").strip(),
                        details=dict(details or {}),
                        confidence=float(cap.get("confidence") or 0.0),
                        created_at=now,
                    ),
                )

        if commit:
            self.db.commit()
            self.db.refresh(catalogue)
        else:
            self.db.flush()
        return catalogue
