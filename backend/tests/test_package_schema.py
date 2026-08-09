"""Package schema smoke tests."""

from uuid import uuid4

from app.schemas.package import DocumentPackageOut, PackageAssembleIn, PackageValidationOut


def test_package_assemble_in_defaults():
    body = PackageAssembleIn()
    assert body.snapshot_id is None


def test_package_validation_out():
    result = PackageValidationOut(ok=True, findings=[])
    assert result.ok is True


def test_package_out_requires_ids():
    pkg = DocumentPackageOut(
        id=uuid4(),
        project_id=uuid4(),
        title="Pkg",
        status="draft",
        source_snapshot_id=uuid4(),
    )
    assert pkg.members == []
