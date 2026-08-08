"""Shared FastAPI dependencies."""

from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.constants.roles import ROLE_APPROVER, ROLE_EDITOR, role_allows
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.db.session import get_db
from app.models.user import User
from app.services.auth_service import AuthService

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise UnauthorizedError("Missing bearer token")
    return AuthService(db).get_user_from_token(credentials.credentials)


def get_editor_user(user: Annotated[User, Depends(get_current_user)]) -> User:
    if not role_allows(user.role, ROLE_EDITOR):
        raise ForbiddenError("Editor role or higher is required")
    return user


def get_approver_user(user: Annotated[User, Depends(get_current_user)]) -> User:
    if not role_allows(user.role, ROLE_APPROVER):
        raise ForbiddenError("Approver role is required for this action")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
EditorUser = Annotated[User, Depends(get_editor_user)]
ApproverUser = Annotated[User, Depends(get_approver_user)]
DbSession = Annotated[Session, Depends(get_db)]

__all__ = [
    "get_db",
    "get_current_user",
    "get_editor_user",
    "get_approver_user",
    "CurrentUser",
    "EditorUser",
    "ApproverUser",
    "DbSession",
]
