"""Auth request/response schemas."""

from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)


class UserPublic(BaseModel):
    id: UUID
    name: str
    email: EmailStr

    model_config = {"from_attributes": True}


class LoginData(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic
