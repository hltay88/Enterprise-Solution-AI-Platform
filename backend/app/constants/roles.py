"""Stage F RBAC MVP — Editor + Approver (approver includes editor privileges)."""

ROLE_EDITOR = "editor"
ROLE_APPROVER = "approver"

VALID_ROLES = frozenset({ROLE_EDITOR, ROLE_APPROVER})

_ROLE_RANK = {
    ROLE_EDITOR: 1,
    ROLE_APPROVER: 2,
}


def normalize_role(role: str | None) -> str:
    cleaned = (role or ROLE_EDITOR).strip().lower()
    if cleaned not in VALID_ROLES:
        return ROLE_EDITOR
    return cleaned


def role_allows(user_role: str | None, minimum: str) -> bool:
    return _ROLE_RANK.get(normalize_role(user_role), 0) >= _ROLE_RANK.get(
        normalize_role(minimum),
        99,
    )
