"""AI provider abstraction. Concrete adapters are added when analysis is implemented."""

from abc import ABC, abstractmethod
from typing import Any


class AIProvider(ABC):
    """Vendor-neutral interface for LLM operations."""

    @abstractmethod
    async def analyze_requirements(self, document_text: str) -> dict[str, Any]:
        """Return structured requirement analysis for the given document text."""

    @abstractmethod
    async def generate_clarifications(
        self,
        analysis: dict[str, Any],
        *,
        document_text: str = "",
        checklist_context: str = "",
        detected_domains: list[str] | None = None,
        min_questions: int = 8,
        max_questions: int = 16,
    ) -> list[str]:
        """Return clarification questions from analysis, source text, and domain packs."""

    @abstractmethod
    async def extract_rkm_draft(self, source_text: str) -> dict[str, Any]:
        """Return structured Draft RKM extraction payload (Stage C)."""

    @abstractmethod
    async def recommend_architecture(
        self,
        published_rkm: dict[str, Any],
        *,
        knowledge_pack_context: str = "",
    ) -> dict[str, Any]:
        """Return vendor-neutral architecture recommendation from a Published RKM."""

    @abstractmethod
    async def recommend_architectures(
        self,
        published_rkm: dict[str, Any],
        *,
        domain_context: str = "",
        pattern_context: str = "",
    ) -> dict[str, Any]:
        """Return one or more architecture candidates from Published RKM + domains."""

    @abstractmethod
    async def identify_solution_domains(
        self,
        published_rkm: dict[str, Any],
        *,
        knowledge_pack_context: str = "",
    ) -> dict[str, Any]:
        """Return Solution Domain Model extraction from a Published RKM."""

    @abstractmethod
    async def generate_proposal_content(
        self,
        snapshot: dict[str, Any],
        content_plan: dict[str, Any],
        *,
        prompt_version: str = "proposal_v1",
    ) -> dict[str, Any]:
        """Return structured proposal content from an immutable source snapshot."""

    @abstractmethod
    async def generate_presentation_content(
        self,
        snapshot: dict[str, Any],
        content_plan: dict[str, Any],
        *,
        prompt_version: str = "presentation_v1",
    ) -> dict[str, Any]:
        """Return structured presentation slides from an immutable source snapshot."""

    @abstractmethod
    async def generate_sow_content(
        self,
        snapshot: dict[str, Any],
        content_plan: dict[str, Any],
        *,
        prompt_version: str = "sow_v1",
    ) -> dict[str, Any]:
        """Return structured SOW content from an immutable source snapshot."""

    @abstractmethod
    async def generate_solution_design_content(
        self,
        snapshot: dict[str, Any],
        content_plan: dict[str, Any],
        *,
        prompt_version: str = "solution_design_v1",
    ) -> dict[str, Any]:
        """Return structured solution design content from an immutable source snapshot."""
