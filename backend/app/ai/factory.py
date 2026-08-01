"""AI provider factory."""

from app.ai.base import AIProvider
from app.ai.fallback_provider import FallbackAIProvider
from app.ai.local_provider import LocalAIProvider
from app.ai.openai_provider import OpenAIProvider
from app.core.config import settings


def get_ai_provider() -> AIProvider:
    """Return the configured provider.

    Modes:
    - openai: OpenAI only
    - local: offline heuristic provider only
    - auto (default): OpenAI first, local fallback on quota/auth/connectivity failures
    """
    mode = (settings.atlas_ai_provider or "auto").strip().lower()

    if mode == "local":
        return LocalAIProvider()

    if mode == "openai":
        return OpenAIProvider()

    # auto
    if settings.openai_api_key:
        return FallbackAIProvider(primary=OpenAIProvider(), fallback=LocalAIProvider())
    return FallbackAIProvider(primary=None, fallback=LocalAIProvider())
