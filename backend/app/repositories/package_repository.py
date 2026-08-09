"""Persistence for Sprint 4.4 document packages."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.deliverable import DocumentPackage, DocumentPackageMember


class PackageRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_package(self, **kwargs: Any) -> DocumentPackage:
        row = DocumentPackage(**kwargs)
        self.db.add(row)
        self.db.flush()
        return row

    def get_package(
        self, package_id: UUID, project_id: UUID
    ) -> DocumentPackage | None:
        return self.db.scalars(
            select(DocumentPackage).where(
                DocumentPackage.id == package_id,
                DocumentPackage.project_id == project_id,
            )
        ).first()

    def list_packages(self, project_id: UUID) -> list[DocumentPackage]:
        return list(
            self.db.scalars(
                select(DocumentPackage)
                .where(DocumentPackage.project_id == project_id)
                .order_by(DocumentPackage.created_at.desc())
            ).all()
        )

    def add_member(self, **kwargs: Any) -> DocumentPackageMember:
        row = DocumentPackageMember(**kwargs)
        self.db.add(row)
        self.db.flush()
        return row

    def list_members(self, package_id: UUID) -> list[DocumentPackageMember]:
        return list(
            self.db.scalars(
                select(DocumentPackageMember)
                .where(DocumentPackageMember.package_id == package_id)
                .order_by(DocumentPackageMember.document_type.asc())
            ).all()
        )

    def touch(self, package: DocumentPackage) -> None:
        package.updated_at = datetime.now(timezone.utc)
        self.db.flush()
