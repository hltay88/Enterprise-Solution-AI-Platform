"""Authentication routes."""

from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.exceptions import UnauthorizedError
from app.core.responses import success_response
from app.db.session import get_db
from app.schemas.auth import LoginData, LoginRequest, UserPublic
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])
bearer_scheme = HTTPBearer(auto_error=False)


@router.post("/login")
def login(body: LoginRequest, db: Session = Depends(get_db)) -> dict:
    data: LoginData = AuthService(db).login(
        email=body.email,
        password=body.password,
    )
    return success_response(data=data.model_dump(mode="json"))


@router.get("/me")
def me(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> dict:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise UnauthorizedError("Missing bearer token")

    user = AuthService(db).get_user_from_token(credentials.credentials)
    return success_response(data=UserPublic.model_validate(user).model_dump(mode="json"))
