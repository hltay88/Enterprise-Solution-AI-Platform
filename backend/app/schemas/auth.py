"""Auth request/response schemas."""

from uuid import UUID

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
<<<<<<< HEAD
    # Use plain str so local/demo domains (e.g. example.com) are accepted.
=======
    # Use plain str so local/demo domains are accepted by validation.
>>>>>>> e40cc55cd54b7a17d53501fc8b9a95f4a28c2cab
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
