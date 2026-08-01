"""OpenAI adapter for the AIProvider interface (ATLAS-012)."""

import json
import logging
from pathlib import Path
from typing import Any, NoReturn

from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AsyncOpenAI,
    AuthenticationError,
    BadRequestError,
    OpenAIError,
    RateLimitError,
)

from app.ai.base import AIProvider
from app.core.config import settings
from app.core.exceptions import AppError, ValidationAppError

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).resolve().parents[2] / "prompts"


def _sanitize_api_key(api_key: str | None) -> str | None:
    if api_key is None:
        return None
    cleaned = api_key.strip().strip('"').strip("'").strip()
    return cleaned or None


def _build_client(api_key: str | None = None) -> tuple[AsyncOpenAI, str, str]:
    raw = settings.openai_api_key if api_key is None else api_key
    key = _sanitize_api_key(raw)
    if not key:
        raise ValidationAppError(
            "OPENAI_API_KEY is not configured. Set it in your .env file, then recreate "
            "the backend container so the key is loaded.",
        )
    model = (settings.openai_model or "gpt-4o-mini").strip() or "gpt-4o-mini"
    return AsyncOpenAI(api_key=key), key, model


async def probe_openai_connection(api_key: str | None = None) -> None:
    """Validate the configured key with a lightweight OpenAI API call."""
    client, _, _ = _build_client(api_key)
    try:
        # models.list authenticates without incurring a chat completion charge
        await client.models.list()
    except Exception as exc:
        _raise_provider_error("validate API key", exc)


class OpenAIProvider(AIProvider):
    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self.client, _, default_model = _build_client(api_key)
        self.model = (model or default_model).strip() or default_model

    async def analyze_requirements(self, document_text: str) -> dict[str, Any]:
        system_prompt = _load_prompt("requirement_analysis.txt")
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                temperature=0.2,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": (
                            "Analyze the following customer requirement text:\n\n"
                            f"{document_text}"
                        ),
                    },
                ],
            )
        except Exception as exc:
            _raise_provider_error("analyze requirements", exc)

        content = response.choices[0].message.content
        if not content:
            raise AppError(
                "INTERNAL_ERROR",
                "AI provider returned an empty analysis response",
                status_code=502,
            )

        try:
            payload = json.loads(content)
        except json.JSONDecodeError as exc:
            raise AppError(
                "INTERNAL_ERROR",
                "AI provider returned invalid JSON",
                status_code=502,
            ) from exc

        return _normalize_analysis(payload)

    async def generate_clarifications(self, analysis: dict[str, Any]) -> list[str]:
        system_prompt = _load_prompt("clarification_questions.txt")
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                temperature=0.3,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": "Create clarification questions for this analysis:\n"
                        + json.dumps(analysis),
                    },
                ],
            )
        except Exception as exc:
            _raise_provider_error("generate clarifications", exc)

        content = response.choices[0].message.content
        if not content:
            raise AppError(
                "INTERNAL_ERROR",
                "AI provider returned an empty clarification response",
                status_code=502,
            )

        try:
            payload = json.loads(content)
        except json.JSONDecodeError as exc:
            raise AppError(
                "INTERNAL_ERROR",
                "AI provider returned invalid JSON for clarifications",
                status_code=502,
            ) from exc

        questions = payload.get("questions", [])
        if not isinstance(questions, list):
            return []
        return [str(item).strip() for item in questions if str(item).strip()]


def _raise_provider_error(action: str, exc: Exception) -> NoReturn:
    """Map OpenAI SDK errors to actionable API messages (never include secrets)."""
    logger.exception("OpenAI failed to %s", action)

    if isinstance(exc, AuthenticationError):
        raise AppError(
            "INTERNAL_ERROR",
            "OpenAI authentication failed. Check that OPENAI_API_KEY is valid "
            "and recreate the backend container after updating .env.",
            status_code=502,
        ) from exc

    if isinstance(exc, RateLimitError):
        raise AppError(
            "INTERNAL_ERROR",
            "OpenAI rate limit or quota exceeded. Check billing and usage limits "
            "at platform.openai.com.",
            status_code=502,
        ) from exc

    if isinstance(exc, APITimeoutError):
        raise AppError(
            "INTERNAL_ERROR",
            "OpenAI request timed out. Please retry analysis.",
            status_code=502,
        ) from exc

    if isinstance(exc, APIConnectionError):
        raise AppError(
            "INTERNAL_ERROR",
            "Could not reach OpenAI from the backend container. "
            "Check Docker network/outbound internet access.",
            status_code=502,
        ) from exc

    if isinstance(exc, BadRequestError):
        detail = _safe_openai_message(exc)
        raise AppError(
            "INTERNAL_ERROR",
            f"OpenAI rejected the analysis request: {detail}",
            status_code=502,
        ) from exc

    if isinstance(exc, APIStatusError):
        detail = _safe_openai_message(exc)
        raise AppError(
            "INTERNAL_ERROR",
            f"OpenAI API error (HTTP {exc.status_code}): {detail}",
            status_code=502,
        ) from exc

    if isinstance(exc, OpenAIError):
        detail = _safe_openai_message(exc)
        raise AppError(
            "INTERNAL_ERROR",
            f"OpenAI error while trying to {action}: {detail}",
            status_code=502,
        ) from exc

    raise AppError(
        "INTERNAL_ERROR",
        f"AI provider failed to {action}",
        status_code=502,
    ) from exc


def _safe_openai_message(exc: Exception) -> str:
    message = getattr(exc, "message", None) or str(exc)
    cleaned = " ".join(str(message).split())
    if len(cleaned) > 240:
        cleaned = cleaned[:237] + "..."
    # Avoid accidentally echoing key-like tokens if SDK includes them.
    lowered = cleaned.lower()
    if "sk-" in lowered or "api_key" in lowered or "authorization" in lowered:
        return "see backend logs for details"
    return cleaned or "see backend logs for details"


def _load_prompt(filename: str) -> str:
    path = PROMPTS_DIR / filename
    if not path.exists():
        raise AppError(
            "INTERNAL_ERROR",
            f"Missing prompt file: {filename}",
            status_code=500,
        )
    return path.read_text(encoding="utf-8").strip()


def _normalize_analysis(payload: dict[str, Any]) -> dict[str, str]:
    keys = [
        "business_objectives",
        "functional_requirements",
        "non_functional_requirements",
        "assumptions",
        "risks",
    ]
    normalized: dict[str, str] = {}
    for key in keys:
        value = payload.get(key, "")
        if isinstance(value, list):
            normalized[key] = "\n".join(str(item).strip() for item in value if str(item).strip())
        else:
            normalized[key] = str(value or "").strip()
    return normalized
