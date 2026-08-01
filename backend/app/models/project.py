"""Project model."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.clarification_question import ClarificationQuestion
    from app.models.requirement_analysis import RequirementAnalysis
    from app.models.requirement_document import RequirementDocument
    from app.models.user import User


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    project_name: Mapped[str] = mapped_column(Text, nullable=False)
    customer: Mapped[str | None] = mapped_column(Text)
    industry: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default="draft")
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

    user: Mapped[User] = relationship("User", back_populates="projects")
    documents: Mapped[list[RequirementDocument]] = relationship(
        "RequirementDocument",
        back_populates="project",
        cascade="all, delete-orphan",
    )
    analyses: Mapped[list[RequirementAnalysis]] = relationship(
        "RequirementAnalysis",
        back_populates="project",
        cascade="all, delete-orphan",
    )
    clarification_questions: Mapped[list[ClarificationQuestion]] = relationship(
        "ClarificationQuestion",
        back_populates="project",
        cascade="all, delete-orphan",
    )
