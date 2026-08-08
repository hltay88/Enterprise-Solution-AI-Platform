"""Requirement Knowledge Model aggregate root."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RequirementModel(Base):
    __tablename__ = "requirement_models"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(Text, nullable=False, default="ai_generated")
    version_major: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    version_minor: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    version_patch: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    version_label: Mapped[str] = mapped_column(Text, nullable=False, default="1.0.0")
    is_active_draft: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    completeness_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    consistency_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    evidence_coverage: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    reasoning_summary: Mapped[str | None] = mapped_column(Text)
    prompt_version: Mapped[str | None] = mapped_column(Text)
    model: Mapped[str | None] = mapped_column(Text)
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
