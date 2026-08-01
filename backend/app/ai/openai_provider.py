"""OpenAI adapter for the AIProvider interface (ATLAS-012)."""

import json
from pathlib import Path
from typing import Any

from openai import AsyncOpenAI

from app.ai.base import AIProvider
from app.core.config import settings
from app.core.exceptions import AppError, ValidationAppError

PROMPTS_DIR = Path(__file__).resolve().parents[2] / "prompts"


class OpenAIProvider(AIProvider):
    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        key = api_key if api_key is not None else settings.openai_api_key
        if not key:
            raise ValidationAppError(
                "OPENAI_API_KEY is not configured. Set it in your environment to run analysis.",
            )
        self.model = model or settings.openai_model
        self.client = AsyncOpenAI(api_key=key)

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
            raise AppError(
                "INTERNAL_ERROR",
                "AI provider failed to analyze requirements",
                status_code=502,
            ) from exc

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
            raise AppError(
                "INTERNAL_ERROR",
                "AI provider failed to generate clarifications",
                status_code=502,
            ) from exc

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
