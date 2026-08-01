"""Authentication business logic."""

from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import UnauthorizedError
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginData, UserPublic


class AuthService:
    def __init__(self, db: Session) -> None:
        self.users = UserRepository(db)

    def login(self, *, email: str, password: str) -> LoginData:
        user = self.users.get_by_email(email.lower().strip())
        if user is None or not verify_password(password, user.password_hash):
            raise UnauthorizedError("Invalid email or password")

        token = create_access_token(user_id=user.id, email=user.email)
        return LoginData(
            access_token=token,
            user=UserPublic.model_validate(user),
        )

    def get_user_from_token(self, token: str) -> User:
        payload = decode_access_token(token)
        subject = payload.get("sub")
        if not subject:
            raise UnauthorizedError("Invalid token payload")

        try:
            user_id = UUID(subject)
        except ValueError as exc:
            raise UnauthorizedError("Invalid token subject") from exc

        user = self.users.get_by_id(user_id)
        if user is None:
            raise UnauthorizedError("User not found")
        return user


def ensure_demo_user(db: Session, *, name: str, email: str, password: str) -> User:
    """Create the Sprint 1 demo user if missing."""
    repo = UserRepository(db)
    existing = repo.get_by_email(email.lower().strip())
    if existing is not None:
        return existing
    return repo.create(
        name=name,
        email=email.lower().strip(),
        password_hash=hash_password(password),
    )
