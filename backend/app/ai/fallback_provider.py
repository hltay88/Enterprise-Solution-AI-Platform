"""Try OpenAI first; fall back to local heuristics when quota/auth blocks analysis."""

from __future__ import annotations

import logging
from typing import Any

from app.ai.base import AIProvider
from app.ai.local_provider import LocalAIProvider
from app.core.exceptions import AppError

logger = logging.getLogger(__name__)

_FALLBACK_CODES = {"AI_QUOTA_EXCEEDED", "AI_AUTH_FAILED", "AI_UNAVAILABLE"}


class FallbackAIProvider(AIProvider):
    def __init__(
        self,
        primary: AIProvider | None,
        fallback: AIProvider | None = None,
    ) -> None:
        self.primary = primary
        self.fallback = fallback or LocalAIProvider()

    async def analyze_requirements(self, document_text: str) -> dict[str, Any]:
        if self.primary is None:
            result = await self.fallback.analyze_requirements(document_text)
            return _mark_local(result, reason="OpenAI was not configured")

        try:
            result = await self.primary.analyze_requirements(document_text)
            result = dict(result)
            result.setdefault("provider", "openai")
            return result
        except AppError as exc:
            if exc.code not in _FALLBACK_CODES:
                raise
            logger.warning(
                "OpenAI analysis unavailable (%s); using local fallback",
                exc.code,
            )
            result = await self.fallback.analyze_requirements(document_text)
            return _mark_local(result, reason=exc.message)

    async def generate_clarifications(self, analysis: dict[str, Any]) -> list[str]:
        if self.primary is None:
            return await self.fallback.generate_clarifications(analysis)

        try:
            return await self.primary.generate_clarifications(analysis)
        except AppError as exc:
            if exc.code not in _FALLBACK_CODES:
                raise
            logger.warning(
                "OpenAI clarifications unavailable (%s); using local fallback",
                exc.code,
            )
            return await self.fallback.generate_clarifications(analysis)


def _mark_local(result: dict[str, Any], reason: str) -> dict[str, Any]:
    payload = dict(result)
    note = (
        "Generated with local fallback because OpenAI was unavailable "
        f"({reason}). Add billing/quota at platform.openai.com to use GPT analysis."
    )
    assumptions = str(payload.get("assumptions") or "").strip()
    payload["assumptions"] = f"{assumptions}\n- {note}".strip() if assumptions else f"- {note}"
    payload["provider"] = "local-fallback"
    payload["fallback_reason"] = reason
    return payload
