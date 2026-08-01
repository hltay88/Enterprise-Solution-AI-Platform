"""Clarification question persistence."""

from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.clarification_question import ClarificationQuestion


class ClarificationRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_for_project(self, project_id: UUID) -> list[ClarificationQuestion]:
        statement = (
            select(ClarificationQuestion)
            .where(ClarificationQuestion.project_id == project_id)
            .order_by(ClarificationQuestion.created_at.asc())
        )
        return list(self.db.scalars(statement).all())

    def replace_for_project(
        self,
        *,
        project_id: UUID,
        questions: list[str],
    ) -> list[ClarificationQuestion]:
        self.db.execute(
            delete(ClarificationQuestion).where(
                ClarificationQuestion.project_id == project_id,
            ),
        )
        rows = [
            ClarificationQuestion(
                project_id=project_id,
                question=question,
                status="open",
            )
            for question in questions
        ]
        self.db.add_all(rows)
        self.db.commit()
        for row in rows:
            self.db.refresh(row)
        return rows
