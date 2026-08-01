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
