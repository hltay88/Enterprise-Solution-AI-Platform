"""Requirement analysis persistence."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.requirement_analysis import RequirementAnalysis


class AnalysisRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_latest_for_project(self, project_id: UUID) -> RequirementAnalysis | None:
        statement = (
            select(RequirementAnalysis)
            .where(RequirementAnalysis.project_id == project_id)
            .order_by(RequirementAnalysis.created_at.desc())
            .limit(1)
        )
        return self.db.scalar(statement)

    def create(
        self,
        *,
        project_id: UUID,
        business_objectives: str,
        functional_requirements: str,
        non_functional_requirements: str,
        assumptions: str,
        risks: str,
        analysis_json: dict,
    ) -> RequirementAnalysis:
        row = RequirementAnalysis(
            project_id=project_id,
            business_objectives=business_objectives,
            functional_requirements=functional_requirements,
            non_functional_requirements=non_functional_requirements,
            assumptions=assumptions,
            risks=risks,
            analysis_json=analysis_json,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row
