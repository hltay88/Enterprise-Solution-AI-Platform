"""AI provider factory."""

from app.ai.base import AIProvider
from app.ai.openai_provider import OpenAIProvider


def get_ai_provider() -> AIProvider:
    """Return the configured default provider (OpenAI for Sprint 1)."""
    return OpenAIProvider()
