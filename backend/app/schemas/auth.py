"""Auth request/response schemas."""

from uuid import UUID

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    # Use plain str so local/demo domains are accepted by validation.
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=1)


class UserPublic(BaseModel):
    id: UUID
    name: str
    email: str

    model_config = {"from_attributes": True}


class LoginData(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic
