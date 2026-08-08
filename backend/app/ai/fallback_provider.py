"""Try cloud providers in order; fall back when quota/auth/connectivity blocks them."""

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
        providers: list[AIProvider] | None = None,
        *,
        primary: AIProvider | None = None,
        fallback: AIProvider | None = None,
    ) -> None:
        if providers is not None:
            chain = list(providers)
        else:
            chain = [item for item in (primary, fallback) if item is not None]
        if not chain:
            chain = [LocalAIProvider()]
        # Guarantee a local last resort for auto mode chains.
        if not any(isinstance(item, LocalAIProvider) for item in chain):
            chain.append(LocalAIProvider())
        self.providers = chain

    async def analyze_requirements(self, document_text: str) -> dict[str, Any]:
        errors: list[str] = []
        for index, provider in enumerate(self.providers):
            name = provider.__class__.__name__
            try:
                result = await provider.analyze_requirements(document_text)
                payload = dict(result)
                payload.setdefault("provider", name.replace("Provider", "").lower())
                if index > 0 and isinstance(provider, LocalAIProvider):
                    return _mark_local(payload, reason="; ".join(errors) or "cloud provider unavailable")
                if index > 0:
                    logger.warning("Using fallback provider %s after earlier failures", name)
                return payload
            except AppError as exc:
                is_last = index == len(self.providers) - 1
                if exc.code not in _FALLBACK_CODES or is_last:
                    raise
                errors.append(f"{name}: {exc.message}")
                logger.warning("%s unavailable (%s); trying next provider", name, exc.code)

        raise AppError("INTERNAL_ERROR", "No AI provider available", status_code=502)

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
        for index, provider in enumerate(self.providers):
            name = provider.__class__.__name__
            try:
                return await provider.generate_clarifications(
                    analysis,
                    document_text=document_text,
                    checklist_context=checklist_context,
                    detected_domains=detected_domains,
                    min_questions=min_questions,
                    max_questions=max_questions,
                )
            except AppError as exc:
                is_last = index == len(self.providers) - 1
                if exc.code not in _FALLBACK_CODES or is_last:
                    raise
                logger.warning(
                    "%s clarifications unavailable (%s); trying next provider",
                    name,
                    exc.code,
                )

        raise AppError("INTERNAL_ERROR", "No AI provider available", status_code=502)

    async def extract_rkm_draft(self, source_text: str) -> dict[str, Any]:
        errors: list[str] = []
        for index, provider in enumerate(self.providers):
            name = provider.__class__.__name__
            try:
                result = await provider.extract_rkm_draft(source_text)
                payload = dict(result)
                payload.setdefault("provider", name.replace("Provider", "").lower())
                if index > 0 and isinstance(provider, LocalAIProvider):
                    payload["fallback_reason"] = "; ".join(errors) or "cloud provider unavailable"
                    summary = str(payload.get("reasoning_summary") or "").strip()
                    note = (
                        "Generated with local fallback because cloud AI providers were "
                        f"unavailable ({payload['fallback_reason']})."
                    )
                    payload["reasoning_summary"] = f"{summary} {note}".strip()
                    payload["provider"] = "local-fallback"
                elif index > 0:
                    logger.warning("Using fallback provider %s for RKM extraction", name)
                return payload
            except AppError as exc:
                is_last = index == len(self.providers) - 1
                if exc.code not in _FALLBACK_CODES or is_last:
                    raise
                errors.append(f"{name}: {exc.message}")
                logger.warning("%s RKM extract unavailable (%s); trying next", name, exc.code)

        raise AppError("INTERNAL_ERROR", "No AI provider available", status_code=502)


def _mark_local(result: dict[str, Any], reason: str) -> dict[str, Any]:
    payload = dict(result)
    note = (
        "Generated with local fallback because cloud AI providers were unavailable "
        f"({reason}). Configure GEMINI_API_KEY for free-tier Gemini analysis."
    )
    assumptions = str(payload.get("assumptions") or "").strip()
    payload["assumptions"] = f"{assumptions}\n- {note}".strip() if assumptions else f"- {note}"
    payload["provider"] = "local-fallback"
    payload["fallback_reason"] = reason
    return payload
