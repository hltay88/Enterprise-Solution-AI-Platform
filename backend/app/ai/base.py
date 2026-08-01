"""AI provider abstraction. Concrete adapters are added when analysis is implemented."""

from abc import ABC, abstractmethod
from typing import Any


class AIProvider(ABC):
    """Vendor-neutral interface for LLM operations."""

    @abstractmethod
    async def analyze_requirements(self, document_text: str) -> dict[str, Any]:
        """Return structured requirement analysis for the given document text."""

    @abstractmethod
    async def generate_clarifications(self, analysis: dict[str, Any]) -> list[str]:
        """Return clarification questions derived from an analysis result."""
