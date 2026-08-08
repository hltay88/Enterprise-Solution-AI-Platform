from app.schemas.audit import AuditLogOut
from datetime import datetime, timezone
from uuid import uuid4


def test_audit_log_out_serializes_metadata_alias():
    row = AuditLogOut(
        id=uuid4(),
        project_id=uuid4(),
        user_id=uuid4(),
        action="rkm.publish",
        resource_type="requirement_model",
        resource_id=uuid4(),
        summary="Published",
        metadata_json={"version_label": "1.0.1"},
        created_at=datetime.now(timezone.utc),
    )
    dumped = row.model_dump(mode="json", by_alias=True)
    assert dumped["metadata"]["version_label"] == "1.0.1"
    assert "metadata_json" not in dumped
