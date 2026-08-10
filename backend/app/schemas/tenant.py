"""Sprint 5.5 — tenant API schemas."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field


class TenantOut(BaseModel):
    id: UUID
    name: str
    slug: str
    status: str
    role: str | None = None


class MemberOut(BaseModel):
    membership_id: UUID
    user_id: UUID
    email: str
    name: str
    role: str


class MemberCreateIn(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    role: str = Field(default="editor", max_length=32)
