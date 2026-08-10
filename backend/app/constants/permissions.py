"""Sprint 5.4 — explicit permission catalog mapped from editor/approver roles."""

from __future__ import annotations

from app.constants.roles import ROLE_APPROVER, ROLE_EDITOR, normalize_role, role_allows

# Permission codes
PERM_COMMENT = "comment.create"
PERM_REVIEW_CREATE = "review_request.create"
PERM_REVIEW_COMPLETE = "review_request.complete"
PERM_APPROVAL_CREATE = "approval_request.create"
PERM_APPROVAL_RESOLVE = "approval_request.resolve"
PERM_AUDIT_VIEW = "audit.view"
PERM_USAGE_VIEW = "usage.view"

_EDITOR_PERMS = frozenset(
    {
        PERM_COMMENT,
        PERM_REVIEW_CREATE,
        PERM_REVIEW_COMPLETE,
        PERM_APPROVAL_CREATE,
    }
)

_APPROVER_PERMS = _EDITOR_PERMS | frozenset(
    {
        PERM_APPROVAL_RESOLVE,
        PERM_AUDIT_VIEW,
        PERM_USAGE_VIEW,
    }
)


def permissions_for_role(role: str | None) -> frozenset[str]:
    cleaned = normalize_role(role)
    if role_allows(cleaned, ROLE_APPROVER):
        return _APPROVER_PERMS
    if role_allows(cleaned, ROLE_EDITOR):
        return _EDITOR_PERMS
    return frozenset()


def has_permission(role: str | None, permission: str) -> bool:
    return permission in permissions_for_role(role)
