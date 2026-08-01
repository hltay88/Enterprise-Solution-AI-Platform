"""Shared helpers for AI provider adapters."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.core.exceptions import AppError

PROMPTS_DIR = Path(__file__).resolve().parents[2] / "prompts"


def load_prompt(filename: str) -> str:
    path = PROMPTS_DIR / filename
    if not path.exists():
        raise AppError(
            "INTERNAL_ERROR",
            f"Missing prompt file: {filename}",
            status_code=500,
        )
    return path.read_text(encoding="utf-8").strip()


def normalize_analysis(payload: dict[str, Any]) -> dict[str, str]:
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
            normalized[key] = "\n".join(
                str(item).strip() for item in value if str(item).strip()
            )
        else:
            normalized[key] = str(value or "").strip()
    return normalized


def parse_json_object(content: str, *, empty_message: str, invalid_message: str) -> dict[str, Any]:
    if not content or not content.strip():
        raise AppError("INTERNAL_ERROR", empty_message, status_code=502)
    try:
        payload = json.loads(content)
    except json.JSONDecodeError as exc:
        raise AppError("INTERNAL_ERROR", invalid_message, status_code=502) from exc
    if not isinstance(payload, dict):
        raise AppError("INTERNAL_ERROR", invalid_message, status_code=502)
    return payload


def sanitize_secret(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip().strip('"').strip("'").strip()
    return cleaned or None


def clarification_system_prompt(*, min_questions: int, max_questions: int) -> str:
    template = load_prompt("clarification_questions.txt")
    return (
        template.replace("MIN_QUESTIONS", str(min_questions)).replace(
            "MAX_QUESTIONS",
            str(max_questions),
        )
    )


def clarification_user_prompt(
    analysis: dict[str, Any],
    *,
    document_text: str = "",
    checklist_context: str = "",
    detected_domains: list[str] | None = None,
) -> str:
    domains = detected_domains or []
    parts = [
        "Create clarification questions for this Presales opportunity.",
        "",
        "## Structured analysis (JSON)",
        json.dumps(analysis, ensure_ascii=False, indent=2),
    ]
    if domains:
        parts.extend(["", "## Detected solution domains", ", ".join(domains)])
    if checklist_context.strip():
        parts.extend(
            [
                "",
                "## Domain checklist packs (cover unanswered themes)",
                checklist_context.strip(),
            ]
        )
    source = document_text.strip()
    if source:
        # Keep prompts bounded for smaller models / free tiers.
        if len(source) > 40_000:
            source = source[:40_000] + "\n\n[truncated]"
        parts.extend(["", "## Original requirement / sales intake source text", source])
    else:
        parts.extend(
            [
                "",
                "## Original requirement / sales intake source text",
                "(not available — rely on analysis and checklist packs)",
            ]
        )
    return "\n".join(parts)


def extract_questions(payload: dict[str, Any]) -> list[str]:
    questions = payload.get("questions", [])
    if not isinstance(questions, list):
        return []
    return [str(item).strip() for item in questions if str(item).strip()]
