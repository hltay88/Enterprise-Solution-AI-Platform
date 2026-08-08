from app.constants.roles import ROLE_APPROVER, ROLE_EDITOR, normalize_role, role_allows


def test_role_allows_editor_minimum():
    assert role_allows(ROLE_EDITOR, ROLE_EDITOR)
    assert role_allows(ROLE_APPROVER, ROLE_EDITOR)
    assert not role_allows(ROLE_EDITOR, ROLE_APPROVER)
    assert role_allows(ROLE_APPROVER, ROLE_APPROVER)


def test_normalize_unknown_role_defaults_to_editor():
    assert normalize_role(None) == ROLE_EDITOR
    assert normalize_role("admin") == ROLE_EDITOR
    assert normalize_role("Approver") == ROLE_APPROVER
