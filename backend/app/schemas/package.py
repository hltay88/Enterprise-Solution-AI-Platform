"""Sprint 4.4 — document package schemas (ATLAS-050)."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


class PackageAssembleIn(BaseModel):
    snapshot_id: UUID | None = None
    architecture_id: UUID | None = None
    title: str | None = None


class PackageApproveIn(BaseModel):
    decision: Literal["approved", "changes_requested"] = "approved"
    note: str | None = None


class PackageMemberOut(BaseModel):
    id: UUID
    package_id: UUID
    document_id: UUID
    document_version_id: UUID
    document_type: str
    role: str = "required"
    title: str | None = None
    document_status: str | None = None
    checksum_sha256: str | None = None


class PackageFinding(BaseModel):
    code: str
    message: str
    severity: str = "error"
    document_type: str | None = None


class PackageValidationOut(BaseModel):
    ok: bool
    findings: list[PackageFinding] = Field(default_factory=list)


class DocumentPackageOut(BaseModel):
    id: UUID
    project_id: UUID
    title: str
    status: str
    version_label: str | None = None
    source_snapshot_id: UUID
    bom_import_id: UUID | None = None
    architecture_id: UUID | None = None
    validation_json: dict[str, Any] = Field(default_factory=dict)
    findings_json: list[Any] = Field(default_factory=list)
    members: list[PackageMemberOut] = Field(default_factory=list)
    export_storage_path: str | None = None
    export_checksum_sha256: str | None = None
    exported_at: datetime | None = None
    created_by: UUID | None = None
    approved_by: UUID | None = None
    approved_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class PackageExportOut(BaseModel):
    package_id: UUID
    status: str
    storage_path: str | None = None
    checksum_sha256: str | None = None
    download_name: str | None = None
    error: str | None = None
    exported_at: datetime | None = None
