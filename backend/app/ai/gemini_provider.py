"""Google Gemini adapter for the AIProvider interface (ATLAS-012)."""

from __future__ import annotations

import json
import logging
from typing import Any, NoReturn

from google import genai
from google.genai import errors as genai_errors
from google.genai import types

from app.ai.base import AIProvider
from app.ai.common import load_prompt, normalize_analysis, parse_json_object, sanitize_secret
from app.core.config import settings
from app.core.exceptions import AppError, ValidationAppError

logger = logging.getLogger(__name__)


def _build_client(api_key: str | None = None) -> tuple[genai.Client, str, str]:
    raw = settings.gemini_api_key if api_key is None else api_key
    key = sanitize_secret(raw)
    if not key:
        raise ValidationAppError(
            "GEMINI_API_KEY is not configured. Get a free key from Google AI Studio "
            "and set it in your repo-root .env, then recreate the backend container.",
        )
    model = (settings.gemini_model or "gemini-2.0-flash").strip() or "gemini-2.0-flash"
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
        user_prompt = (
            "Analyze the following customer requirement text:\n\n" + document_text
        )
        try:
            response = await self.client.aio.models.generate_content(
                model=self.model,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.2,
                    response_mime_type="application/json",
                ),
            )
        except Exception as exc:  # noqa: BLE001
            _raise_provider_error("analyze requirements", exc)

        payload = parse_json_object(
            response.text or "",
            empty_message="AI provider returned an empty analysis response",
            invalid_message="AI provider returned invalid JSON",
        )
        result = normalize_analysis(payload)
        result["provider"] = "gemini"
        return result

    async def generate_clarifications(self, analysis: dict[str, Any]) -> list[str]:
        system_prompt = load_prompt("clarification_questions.txt")
        user_prompt = "Create clarification questions for this analysis:\n" + json.dumps(
            analysis
        )
        try:
            response = await self.client.aio.models.generate_content(
                model=self.model,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.3,
                    response_mime_type="application/json",
                ),
            )
        except Exception as exc:  # noqa: BLE001
            _raise_provider_error("generate clarifications", exc)

        payload = parse_json_object(
            response.text or "",
            empty_message="AI provider returned an empty clarification response",
            invalid_message="AI provider returned invalid JSON for clarifications",
        )
        questions = payload.get("questions", [])
        if not isinstance(questions, list):
            return []
        return [str(item).strip() for item in questions if str(item).strip()]


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
    if "api key" in lowered or "apikey" in lowered or "aiza" in lowered:
        return "see backend logs for details"
    return cleaned or "see backend logs for details"
