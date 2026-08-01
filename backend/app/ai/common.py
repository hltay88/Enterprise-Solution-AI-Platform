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
