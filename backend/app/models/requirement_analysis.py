"""Requirement analysis model."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.project import Project


class RequirementAnalysis(Base):
    __tablename__ = "requirement_analysis"

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
    business_objectives: Mapped[str | None] = mapped_column(Text)
    functional_requirements: Mapped[str | None] = mapped_column(Text)
    non_functional_requirements: Mapped[str | None] = mapped_column(Text)
    assumptions: Mapped[str | None] = mapped_column(Text)
    risks: Mapped[str | None] = mapped_column(Text)
    analysis_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    project: Mapped[Project] = relationship("Project", back_populates="analyses")
