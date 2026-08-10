"""Sprint 5.4 — permissions and collaboration contracts (no DB)."""

from app.constants.permissions import (
    PERM_APPROVAL_RESOLVE,
    PERM_AUDIT_VIEW,
    PERM_COMMENT,
    PERM_USAGE_VIEW,
    has_permission,
    permissions_for_role,
)
from app.constants.roles import ROLE_APPROVER, ROLE_EDITOR
from app.schemas.collaboration import (
    ApprovalRequestCreate,
    ApprovalRequestResolve,
    CommentCreate,
    ReviewRequestCreate,
    UsageSummaryOut,
)


def test_editor_permissions_matrix():
    perms = permissions_for_role(ROLE_EDITOR)
    assert PERM_COMMENT in perms
    assert PERM_APPROVAL_RESOLVE not in perms
    assert PERM_AUDIT_VIEW not in perms
    assert PERM_USAGE_VIEW not in perms
    assert has_permission(ROLE_EDITOR, PERM_COMMENT)
    assert not has_permission(ROLE_EDITOR, PERM_APPROVAL_RESOLVE)


def test_approver_includes_governance_views():
    perms = permissions_for_role(ROLE_APPROVER)
    assert PERM_COMMENT in perms
    assert PERM_APPROVAL_RESOLVE in perms
    assert PERM_AUDIT_VIEW in perms
    assert PERM_USAGE_VIEW in perms


def test_comment_create_schema_requires_body():
    row = CommentCreate(body=" Looks good ")
    assert row.body.strip() == "Looks good"


def test_review_and_approval_request_schemas():
    review = ReviewRequestCreate(resource_type="architecture", message="Please review")
    assert review.resource_type == "architecture"
    approval = ApprovalRequestCreate(resource_type="rkm")
    assert approval.message == ""
    resolve = ApprovalRequestResolve(decision="approved", resolution_note="OK")
    assert resolve.decision == "approved"


def test_usage_summary_defaults():
    summary = UsageSummaryOut(total=0, success_count=0, failure_count=0)
    assert summary.by_event_type == {}
    assert summary.avg_latency_ms is None
