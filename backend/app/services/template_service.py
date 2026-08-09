"""Resolve versioned document templates (ATLAS-046)."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.deliverable import DocumentTemplate, TemplateVersion
from app.repositories.deliverable_repository import DeliverableRepository


class TemplateService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = DeliverableRepository(db)

    def resolve_proposal_template(
        self,
    ) -> tuple[DocumentTemplate, TemplateVersion]:
        template, version = self.repo.ensure_proposal_template_seed()
        self.db.commit()
        return template, version

    def resolve_presentation_template(
        self,
    ) -> tuple[DocumentTemplate, TemplateVersion]:
        template, version = self.repo.ensure_presentation_template_seed()
        self.db.commit()
        return template, version

    def resolve_sow_template(self) -> tuple[DocumentTemplate, TemplateVersion]:
        template, version = self.repo.ensure_sow_template_seed()
        self.db.commit()
        return template, version

    def resolve_solution_design_template(
        self,
    ) -> tuple[DocumentTemplate, TemplateVersion]:
        template, version = self.repo.ensure_solution_design_template_seed()
        self.db.commit()
        return template, version
