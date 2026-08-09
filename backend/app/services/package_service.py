"""Document package assembly, validation, approval, ZIP export (Sprint 4.4)."""

from __future__ import annotations

import hashlib
import json
import zipfile
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import NotFoundError, ValidationAppError
from app.repositories.deliverable_repository import DeliverableRepository
from app.repositories.package_repository import PackageRepository
from app.repositories.project_repository import ProjectRepository
from app.schemas.deliverable import (
    REQUIRED_PACKAGE_DOCUMENT_TYPES,
    DeliverableGenerateIn,
    SnapshotCreateIn,
)
from app.schemas.package import (
    DocumentPackageOut,
    PackageApproveIn,
    PackageAssembleIn,
    PackageExportOut,
    PackageFinding,
    PackageMemberOut,
    PackageValidationOut,
)
from app.services.audit_service import AuditService
from app.services.bom_generation_service import BomGenerationService
from app.services.export_service import ExportService
from app.services.source_snapshot_service import SourceSnapshotService

_CANONICAL_EXPORT: dict[str, str] = {
    "proposal": "docx",
    "presentation": "pptx",
    "sow": "docx",
    "solution_design": "docx",
    "bom": "xlsx",
}

_REQUIRED_APPROVED = ("proposal", "presentation", "sow", "solution_design")


class PackageService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.projects = ProjectRepository(db)
        self.repo = PackageRepository(db)
        self.deliverables = DeliverableRepository(db)
        self.snapshots = SourceSnapshotService(db)
        self.exports = ExportService(db)
        self.bom = BomGenerationService(db)

    async def assemble(
        self,
        project_id: UUID,
        user_id: UUID,
        body: PackageAssembleIn | None = None,
    ) -> DocumentPackageOut:
        if self.projects.get_for_user(project_id, user_id) is None:
            raise NotFoundError("Project not found")
        body = body or PackageAssembleIn()

        if body.snapshot_id is not None:
            snapshot = self.deliverables.get_snapshot(body.snapshot_id, project_id)
            if snapshot is None:
                raise NotFoundError("Source snapshot not found")
        else:
            created = self.snapshots.create(
                project_id,
                user_id,
                SnapshotCreateIn(architecture_id=body.architecture_id),
            )
            snapshot = self.deliverables.get_snapshot(created.id, project_id)
            assert snapshot is not None

        if not snapshot.bom_validated:
            raise ValidationAppError(
                "Package assembly requires a validated BOM (ATLAS-050)"
            )

        docs_by_type = self._latest_by_type(project_id)
        missing_approved: list[str] = []
        arch_ids: set[str] = set()
        for doc_type in _REQUIRED_APPROVED:
            doc = docs_by_type.get(doc_type)
            if doc is None or str(doc.status).lower() != "approved":
                missing_approved.append(doc_type)
                continue
            snap = self.deliverables.get_snapshot(doc.source_snapshot_id, project_id)
            if snap and snap.architecture_id:
                arch_ids.add(str(snap.architecture_id))
        if missing_approved:
            raise ValidationAppError(
                "Package assembly requires approved deliverables: "
                + ", ".join(missing_approved)
            )
        if snapshot.architecture_id:
            arch_ids.add(str(snapshot.architecture_id))
        if len(arch_ids) > 1:
            raise ValidationAppError(
                "Package members pin different architecture versions: "
                + ", ".join(sorted(arch_ids))
            )

        # Ensure BOM deliverable (auto-approve from validated source)
        bom_doc = docs_by_type.get("bom")
        if (
            bom_doc is None
            or str(bom_doc.status).lower() != "approved"
            or bom_doc.source_snapshot_id != snapshot.id
        ):
            out = await self.bom.generate(
                project_id,
                user_id,
                DeliverableGenerateIn(
                    document_type="bom", snapshot_id=snapshot.id
                ),
                auto_approve=True,
            )
            bom_doc = self.deliverables.get_document(out.id, project_id)
            assert bom_doc is not None
            docs_by_type["bom"] = bom_doc

        bom_meta = (snapshot.payload_json or {}).get("bom") or {}
        bom_import_id = None
        raw_bom_id = bom_meta.get("bom_import_id") or snapshot.bom_import_id
        if raw_bom_id:
            try:
                bom_import_id = UUID(str(raw_bom_id))
            except ValueError:
                bom_import_id = None

        package = self.repo.create_package(
            project_id=project_id,
            title=body.title or "Customer Document Package",
            status="draft",
            version_label="1.0.0",
            source_snapshot_id=snapshot.id,
            bom_import_id=bom_import_id,
            architecture_id=snapshot.architecture_id,
            validation_json={},
            findings_json=[],
            created_by=user_id,
        )

        for doc_type in REQUIRED_PACKAGE_DOCUMENT_TYPES:
            doc = docs_by_type.get(doc_type)
            if doc is None or doc.current_version_id is None:
                raise ValidationAppError(f"Missing package member: {doc_type}")
            self.repo.add_member(
                package_id=package.id,
                document_id=doc.id,
                document_version_id=doc.current_version_id,
                document_type=doc_type,
                role="required",
            )

        validation = self._validate_package_row(package, project_id)
        package.validation_json = validation.model_dump(mode="json")
        package.findings_json = [f.model_dump(mode="json") for f in validation.findings]
        package.status = "validated" if validation.ok else "draft"
        self.repo.touch(package)
        self.db.commit()
        self.db.refresh(package)

        AuditService(self.db).record(
            project_id=project_id,
            user_id=user_id,
            action="package.assemble",
            summary=f"Assembled package '{package.title}'",
            resource_type="document_package",
            resource_id=package.id,
            metadata={"ok": validation.ok, "findings": len(validation.findings)},
        )
        return self.to_out(package, project_id)

    def list_packages(self, project_id: UUID, user_id: UUID) -> list[DocumentPackageOut]:
        if self.projects.get_for_user(project_id, user_id) is None:
            raise NotFoundError("Project not found")
        return [self.to_out(p, project_id) for p in self.repo.list_packages(project_id)]

    def get(self, project_id: UUID, package_id: UUID, user_id: UUID) -> DocumentPackageOut:
        if self.projects.get_for_user(project_id, user_id) is None:
            raise NotFoundError("Project not found")
        package = self.repo.get_package(package_id, project_id)
        if package is None:
            raise NotFoundError("Package not found")
        return self.to_out(package, project_id)

    def validate(
        self, project_id: UUID, package_id: UUID, user_id: UUID
    ) -> PackageValidationOut:
        if self.projects.get_for_user(project_id, user_id) is None:
            raise NotFoundError("Project not found")
        package = self.repo.get_package(package_id, project_id)
        if package is None:
            raise NotFoundError("Package not found")
        result = self._validate_package_row(package, project_id)
        package.validation_json = result.model_dump(mode="json")
        package.findings_json = [f.model_dump(mode="json") for f in result.findings]
        if result.ok and package.status in {"draft", "validated"}:
            package.status = "validated"
        self.repo.touch(package)
        self.db.commit()
        AuditService(self.db).record(
            project_id=project_id,
            user_id=user_id,
            action="package.validate",
            summary=f"Validated package ({'ok' if result.ok else 'issues'})",
            resource_type="document_package",
            resource_id=package.id,
            metadata={"ok": result.ok},
        )
        return result

    def approve(
        self,
        project_id: UUID,
        package_id: UUID,
        user_id: UUID,
        body: PackageApproveIn | None = None,
    ) -> DocumentPackageOut:
        if self.projects.get_for_user(project_id, user_id) is None:
            raise NotFoundError("Project not found")
        body = body or PackageApproveIn()
        package = self.repo.get_package(package_id, project_id)
        if package is None:
            raise NotFoundError("Package not found")
        if package.status == "approved" and body.decision == "approved":
            return self.to_out(package, project_id)

        validation = self._validate_package_row(package, project_id)
        package.validation_json = validation.model_dump(mode="json")
        package.findings_json = [f.model_dump(mode="json") for f in validation.findings]

        if body.decision == "changes_requested":
            package.status = "draft"
            package.approved_by = None
            package.approved_at = None
            self.repo.touch(package)
            self.db.commit()
            AuditService(self.db).record(
                project_id=project_id,
                user_id=user_id,
                action="package.changes_requested",
                summary="Requested changes on package",
                resource_type="document_package",
                resource_id=package.id,
                metadata={"note": body.note},
            )
            return self.to_out(package, project_id)

        if not validation.ok:
            raise ValidationAppError(
                "Cannot approve package while validation errors remain: "
                + "; ".join(f.message for f in validation.findings if f.severity == "error")
            )

        package.status = "approved"
        package.approved_by = user_id
        package.approved_at = datetime.now(timezone.utc)
        self.repo.touch(package)
        self.db.commit()
        AuditService(self.db).record(
            project_id=project_id,
            user_id=user_id,
            action="package.approve",
            summary="Approved document package",
            resource_type="document_package",
            resource_id=package.id,
            metadata={},
        )
        return self.to_out(package, project_id)

    def export_zip(
        self, project_id: UUID, package_id: UUID, user_id: UUID
    ) -> PackageExportOut:
        if self.projects.get_for_user(project_id, user_id) is None:
            raise NotFoundError("Project not found")
        package = self.repo.get_package(package_id, project_id)
        if package is None:
            raise NotFoundError("Package not found")
        if package.status not in {"approved", "exported", "validated"}:
            # Allow validated for convenience, but prefer approved
            if package.status != "validated":
                raise ValidationAppError(
                    "Package must be validated or approved before ZIP export"
                )

        validation = self._validate_package_row(package, project_id)
        if not validation.ok:
            raise ValidationAppError(
                "Package validation failed: "
                + "; ".join(f.message for f in validation.findings if f.severity == "error")
            )

        members = self.repo.list_members(package.id)
        file_entries: list[tuple[str, bytes, str]] = []
        manifest_members: list[dict] = []

        for member in members:
            doc = self.deliverables.get_document(member.document_id, project_id)
            if doc is None:
                raise ValidationAppError(f"Missing member document {member.document_type}")
            fmt = _CANONICAL_EXPORT[member.document_type]
            data, ext = self.exports.render_bytes(doc.id, project_id, fmt)
            filename = f"{member.document_type}.{ext}"
            checksum = hashlib.sha256(data).hexdigest()
            member.checksum_sha256 = checksum
            file_entries.append((filename, data, checksum))
            manifest_members.append(
                {
                    "document_type": member.document_type,
                    "document_id": str(member.document_id),
                    "document_version_id": str(member.document_version_id),
                    "filename": filename,
                    "checksum_sha256": checksum,
                    "title": doc.title,
                    "status": doc.status,
                }
            )

        manifest = {
            "package_id": str(package.id),
            "project_id": str(project_id),
            "title": package.title,
            "version_label": package.version_label,
            "status": package.status,
            "source_snapshot_id": str(package.source_snapshot_id),
            "architecture_id": str(package.architecture_id)
            if package.architecture_id
            else None,
            "bom_import_id": str(package.bom_import_id) if package.bom_import_id else None,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "members": manifest_members,
            "atlas_foundation": "0.4",
        }
        manifest_bytes = json.dumps(manifest, indent=2).encode("utf-8")

        buffer = BytesIO()
        with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("manifest.json", manifest_bytes)
            for filename, data, _ in file_entries:
                zf.writestr(filename, data)
            zf.writestr(
                "appendices/README.txt",
                "Architecture diagram binaries are not generated in Sprint 4.4; "
                "see source snapshot / architecture metadata in Atlas.\n",
            )
        zip_bytes = buffer.getvalue()
        checksum = hashlib.sha256(zip_bytes).hexdigest()

        settings = get_settings()
        out_dir = Path(settings.storage_path) / str(project_id) / "packages"
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / f"{uuid4()}_package.zip"
        path.write_bytes(zip_bytes)

        package.export_storage_path = str(path)
        package.export_checksum_sha256 = checksum
        package.exported_at = datetime.now(timezone.utc)
        if package.status == "approved":
            package.status = "exported"
        self.repo.touch(package)
        self.db.commit()

        AuditService(self.db).record(
            project_id=project_id,
            user_id=user_id,
            action="package.export",
            summary="Exported package ZIP",
            resource_type="document_package",
            resource_id=package.id,
            metadata={"checksum": checksum, "path": str(path)},
        )
        return PackageExportOut(
            package_id=package.id,
            status="completed",
            storage_path=str(path),
            checksum_sha256=checksum,
            download_name=f"{package.title or 'package'}.zip",
            exported_at=package.exported_at,
        )

    def _latest_by_type(self, project_id: UUID) -> dict:
        docs = self.deliverables.list_documents(project_id)
        by_type: dict = {}
        for doc in docs:
            # Prefer approved when choosing first (list is newest-first)
            existing = by_type.get(doc.document_type)
            if existing is None:
                by_type[doc.document_type] = doc
                continue
            if (
                str(doc.status).lower() == "approved"
                and str(existing.status).lower() != "approved"
            ):
                by_type[doc.document_type] = doc
        return by_type

    def _validate_package_row(
        self, package, project_id: UUID
    ) -> PackageValidationOut:
        findings: list[PackageFinding] = []
        members = self.repo.list_members(package.id)
        present = {m.document_type for m in members}
        for required in REQUIRED_PACKAGE_DOCUMENT_TYPES:
            if required not in present:
                findings.append(
                    PackageFinding(
                        code="missing_member",
                        message=f"Required member '{required}' is missing",
                        document_type=required,
                    )
                )

        snapshot = self.deliverables.get_snapshot(package.source_snapshot_id, project_id)
        if snapshot is None:
            findings.append(
                PackageFinding(
                    code="missing_snapshot",
                    message="Package source snapshot not found",
                )
            )
        elif not snapshot.bom_validated:
            findings.append(
                PackageFinding(
                    code="bom_not_validated",
                    message="Package snapshot BOM is not validated",
                )
            )

        arch_ids: set[str] = set()
        if snapshot and snapshot.architecture_id:
            arch_ids.add(str(snapshot.architecture_id))

        for member in members:
            doc = self.deliverables.get_document(member.document_id, project_id)
            if doc is None:
                findings.append(
                    PackageFinding(
                        code="member_missing_document",
                        message=f"Member document missing for {member.document_type}",
                        document_type=member.document_type,
                    )
                )
                continue
            if member.document_type in _REQUIRED_APPROVED and str(doc.status).lower() != "approved":
                findings.append(
                    PackageFinding(
                        code="member_not_approved",
                        message=f"{member.document_type} must be approved",
                        document_type=member.document_type,
                    )
                )
            if member.document_type == "bom" and str(doc.status).lower() not in {
                "approved",
                "exported",
            }:
                # allow draft bom only if auto-approved expected
                if str(doc.status).lower() != "approved":
                    findings.append(
                        PackageFinding(
                            code="bom_not_approved",
                            message="BOM deliverable must be approved for package",
                            document_type="bom",
                            severity="error",
                        )
                    )
            snap = self.deliverables.get_snapshot(doc.source_snapshot_id, project_id)
            if snap and snap.architecture_id:
                arch_ids.add(str(snap.architecture_id))
            if (
                snap
                and snapshot
                and snap.architecture_id
                and snapshot.architecture_id
                and snap.architecture_id != snapshot.architecture_id
            ):
                findings.append(
                    PackageFinding(
                        code="architecture_mismatch",
                        message=(
                            f"{member.document_type} architecture differs from "
                            "package snapshot"
                        ),
                        document_type=member.document_type,
                    )
                )

        if len(arch_ids) > 1:
            findings.append(
                PackageFinding(
                    code="mixed_architectures",
                    message="Package spans multiple architecture IDs: "
                    + ", ".join(sorted(arch_ids)),
                )
            )

        blocking = [f for f in findings if f.severity == "error"]
        return PackageValidationOut(ok=len(blocking) == 0, findings=findings)

    def to_out(self, package, project_id: UUID) -> DocumentPackageOut:
        members_out: list[PackageMemberOut] = []
        for member in self.repo.list_members(package.id):
            doc = self.deliverables.get_document(member.document_id, project_id)
            members_out.append(
                PackageMemberOut(
                    id=member.id,
                    package_id=member.package_id,
                    document_id=member.document_id,
                    document_version_id=member.document_version_id,
                    document_type=member.document_type,
                    role=member.role,
                    title=doc.title if doc else None,
                    document_status=doc.status if doc else None,
                    checksum_sha256=member.checksum_sha256,
                )
            )
        return DocumentPackageOut(
            id=package.id,
            project_id=package.project_id,
            title=package.title,
            status=package.status,
            version_label=package.version_label,
            source_snapshot_id=package.source_snapshot_id,
            bom_import_id=package.bom_import_id,
            architecture_id=package.architecture_id,
            validation_json=package.validation_json or {},
            findings_json=list(package.findings_json or []),
            members=members_out,
            export_storage_path=package.export_storage_path,
            export_checksum_sha256=package.export_checksum_sha256,
            exported_at=package.exported_at,
            created_by=package.created_by,
            approved_by=package.approved_by,
            approved_at=package.approved_at,
            created_at=package.created_at,
            updated_at=package.updated_at,
        )
