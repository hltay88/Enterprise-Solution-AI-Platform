"""AI provider factory."""

from app.ai.base import AIProvider
from app.ai.fallback_provider import FallbackAIProvider
from app.ai.gemini_provider import GeminiProvider
from app.ai.local_provider import LocalAIProvider
from app.ai.openai_provider import OpenAIProvider
from app.core.config import settings


def get_ai_provider() -> AIProvider:
    """Return the configured provider.

    Modes:
    - gemini: Gemini only
    - openai: OpenAI only
    - local: offline heuristic provider only
    - auto (default): Gemini (if keyed) -> OpenAI (if keyed) -> local fallback
    """
    mode = (settings.atlas_ai_provider or "auto").strip().lower()

    if mode == "local":
        return LocalAIProvider()

    if mode == "gemini":
        return GeminiProvider()

    if mode == "openai":
        return OpenAIProvider()

    # auto — prefer free-tier Gemini, then OpenAI, then local
    chain: list[AIProvider] = []
    if settings.effective_gemini_api_key:
        chain.append(GeminiProvider())
    if settings.openai_api_key:
        chain.append(OpenAIProvider())
    chain.append(LocalAIProvider())
    return FallbackAIProvider(providers=chain)
