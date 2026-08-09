"""Google Gemini adapter for the AIProvider interface (ATLAS-012)."""

from __future__ import annotations

import json
import logging
from typing import Any, NoReturn

from google import genai
from google.genai import errors as genai_errors
from google.genai import types

from app.ai.base import AIProvider
from app.ai.common import (
    clarification_system_prompt,
    clarification_user_prompt,
    extract_questions,
    load_prompt,
    normalize_analysis,
    normalize_architecture,
    normalize_domain_identification,
    normalize_rkm_extraction,
    parse_json_object,
    sanitize_secret,
)
from app.core.config import settings
from app.core.exceptions import AppError, ValidationAppError

logger = logging.getLogger(__name__)

# Prefer aliases that remain available to new free-tier keys.
DEFAULT_GEMINI_MODEL = "gemini-flash-latest"
_MODEL_FALLBACKS = (
    "gemini-flash-latest",
    "gemini-flash-lite-latest",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
)


def _build_client(api_key: str | None = None) -> tuple[genai.Client, str, str]:
    raw = settings.effective_gemini_api_key if api_key is None else api_key
    key = sanitize_secret(raw)
    if not key:
        raise ValidationAppError(
            "GEMINI_API_KEY is not configured. Get a free key from Google AI Studio "
            "and set it in your repo-root .env, then recreate the backend container.",
        )
    model = (settings.gemini_model or DEFAULT_GEMINI_MODEL).strip() or DEFAULT_GEMINI_MODEL
    return genai.Client(api_key=key), key, model


async def probe_gemini_connection(api_key: str | None = None) -> None:
    """Validate the configured Gemini key with a lightweight list call."""
    client, _, _ = _build_client(api_key)
    try:
        pager = await client.aio.models.list()
        async for _model in pager:
            break
    except Exception as exc:  # noqa: BLE001
        _raise_provider_error("validate API key", exc)


class GeminiProvider(AIProvider):
    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self.client, _, default_model = _build_client(api_key)
        self.model = (model or default_model).strip() or default_model

    async def analyze_requirements(self, document_text: str) -> dict[str, Any]:
        system_prompt = load_prompt("requirement_analysis.txt")
        user_prompt = "Analyze the following customer requirement text:\n\n" + document_text
        response = await self._generate(
            action="analyze requirements",
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.2,
        )
        payload = parse_json_object(
            response.text or "",
            empty_message="AI provider returned an empty analysis response",
            invalid_message="AI provider returned invalid JSON",
        )
        result = normalize_analysis(payload)
        result["provider"] = "gemini"
        result["model"] = self.model
        return result

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
        system_prompt = clarification_system_prompt(
            min_questions=min_questions,
            max_questions=max_questions,
        )
        user_prompt = clarification_user_prompt(
            analysis,
            document_text=document_text,
            checklist_context=checklist_context,
            detected_domains=detected_domains,
        )
        response = await self._generate(
            action="generate clarifications",
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.3,
        )
        payload = parse_json_object(
            response.text or "",
            empty_message="AI provider returned an empty clarification response",
            invalid_message="AI provider returned invalid JSON for clarifications",
        )
        return extract_questions(payload)

    async def extract_rkm_draft(self, source_text: str) -> dict[str, Any]:
        system_prompt = load_prompt("rkm_extraction.txt")
        user_prompt = (
            "Build a Draft Requirement Knowledge Model from this source text:\n\n"
            + source_text
        )
        response = await self._generate(
            action="extract RKM draft",
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.2,
        )
        payload = parse_json_object(
            response.text or "",
            empty_message="AI provider returned an empty RKM extraction response",
            invalid_message="AI provider returned invalid JSON for RKM extraction",
        )
        result = normalize_rkm_extraction(payload)
        result["provider"] = "gemini"
        result["model"] = self.model
        return result

    async def recommend_architecture(
        self,
        published_rkm: dict[str, Any],
        *,
        knowledge_pack_context: str = "",
    ) -> dict[str, Any]:
        system_prompt = load_prompt("architecture_recommendation.txt")
        pack = knowledge_pack_context.strip()
        user_prompt = (
            "Create a vendor-neutral architecture recommendation from this "
            "Published Requirement Knowledge Model JSON:\n\n"
            + json.dumps(published_rkm, ensure_ascii=True)[:120000]
        )
        if pack:
            user_prompt += (
                "\n\nAdditional vendor-neutral knowledge pack guidance:\n" + pack[:8000]
            )
        response = await self._generate(
            action="recommend architecture",
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.2,
        )
        payload = parse_json_object(
            response.text or "",
            empty_message="AI provider returned an empty architecture response",
            invalid_message="AI provider returned invalid JSON for architecture",
        )
        result = normalize_architecture(payload)
        result["provider"] = "gemini"
        result["model"] = self.model
        return result

    async def identify_solution_domains(
        self,
        published_rkm: dict[str, Any],
        *,
        knowledge_pack_context: str = "",
    ) -> dict[str, Any]:
        system_prompt = load_prompt("domain_identification.txt")
        pack = knowledge_pack_context.strip()
        user_prompt = (
            "Identify solution domains from this Published Requirement Knowledge "
            "Model JSON. Use only catalog domain codes from the knowledge pack "
            "context.\n\n"
            + json.dumps(published_rkm, ensure_ascii=True)[:120000]
        )
        if pack:
            user_prompt += (
                "\n\nPhase 3 domain knowledge pack / catalog context:\n" + pack[:8000]
            )
        response = await self._generate(
            action="identify solution domains",
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.2,
        )
        payload = parse_json_object(
            response.text or "",
            empty_message="AI provider returned an empty domain identification response",
            invalid_message="AI provider returned invalid JSON for domain identification",
        )
        result = normalize_domain_identification(payload)
        result["provider"] = "gemini"
        result["model"] = self.model
        return result

    async def _generate(
        self,
        *,
        action: str,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
    ):
        last_exc: Exception | None = None
        for model in _candidate_models(self.model):
            try:
                response = await self.client.aio.models.generate_content(
                    model=model,
                    contents=user_prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_prompt,
                        temperature=temperature,
                        response_mime_type="application/json",
                    ),
                )
                if model != self.model:
                    logger.warning("Gemini model %s failed; succeeded with %s", self.model, model)
                    self.model = model
                return response
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                if _is_retryable_model_error(exc):
                    logger.warning(
                        "Gemini model %s unavailable for %s (%s); trying next model",
                        model,
                        action,
                        getattr(exc, "code", type(exc).__name__),
                    )
                    continue
                _raise_provider_error(action, exc)

        assert last_exc is not None
        _raise_provider_error(action, last_exc)


def _candidate_models(preferred: str) -> list[str]:
    ordered = [preferred, *_MODEL_FALLBACKS]
    unique: list[str] = []
    for model in ordered:
        cleaned = (model or "").strip()
        if cleaned and cleaned not in unique:
            unique.append(cleaned)
    return unique


def _is_retryable_model_error(exc: Exception) -> bool:
    if not isinstance(exc, genai_errors.APIError):
        return False
    code = int(getattr(exc, "code", 0) or 0)
    message = (getattr(exc, "message", None) or str(exc)).lower()
    if code == 429:
        return True
    if code == 404:
        return True
    if "no longer available" in message or "not found" in message:
        return True
    return False


def _raise_provider_error(action: str, exc: Exception) -> NoReturn:
    logger.exception("Gemini failed to %s", action)

    if isinstance(exc, genai_errors.ClientError):
        code = int(getattr(exc, "code", 0) or 0)
        detail = _safe_message(exc)
        if code in {401, 403}:
            raise AppError(
                "AI_AUTH_FAILED",
                "Gemini authentication failed. Check that GEMINI_API_KEY is valid "
                "and recreate the backend container after updating .env.",
                status_code=502,
            ) from exc
        if code == 429:
            raise AppError(
                "AI_QUOTA_EXCEEDED",
                "Gemini rate limit or quota exceeded. Check usage in Google AI Studio "
                "or retry later.",
                status_code=502,
            ) from exc
        raise AppError(
            "INTERNAL_ERROR",
            f"Gemini rejected the request (HTTP {code}): {detail}",
            status_code=502,
        ) from exc

    if isinstance(exc, genai_errors.ServerError):
        detail = _safe_message(exc)
        raise AppError(
            "AI_UNAVAILABLE",
            f"Gemini service error: {detail}",
            status_code=502,
        ) from exc

    if isinstance(exc, genai_errors.APIError):
        detail = _safe_message(exc)
        code = int(getattr(exc, "code", 0) or 0)
        if code == 429:
            raise AppError(
                "AI_QUOTA_EXCEEDED",
                "Gemini rate limit or quota exceeded. Check usage in Google AI Studio "
                "or retry later.",
                status_code=502,
            ) from exc
        raise AppError(
            "AI_UNAVAILABLE",
            f"Gemini API error: {detail}",
            status_code=502,
        ) from exc

    raise AppError(
        "INTERNAL_ERROR",
        f"AI provider failed to {action}",
        status_code=502,
    ) from exc


def _safe_message(exc: Exception) -> str:
    message = getattr(exc, "message", None) or str(exc)
    cleaned = " ".join(str(message).split())
    if len(cleaned) > 240:
        cleaned = cleaned[:237] + "..."
    lowered = cleaned.lower()
    if "api key" in lowered or "apikey" in lowered or "aiza" in lowered or "aq." in lowered:
        return "see backend logs for details"
    return cleaned or "see backend logs for details"
