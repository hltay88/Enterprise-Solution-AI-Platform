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
from app.ai.common import (
    clarification_system_prompt,
    clarification_user_prompt,
    extract_questions,
    normalize_architecture,
    normalize_architecture_candidates,
    normalize_domain_identification,
    normalize_rkm_extraction,
)
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
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                temperature=0.3,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
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

        return extract_questions(payload)

    async def extract_rkm_draft(self, source_text: str) -> dict[str, Any]:
        system_prompt = _load_prompt("rkm_extraction.txt")
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
                            "Build a Draft Requirement Knowledge Model from this "
                            f"source text:\n\n{source_text}"
                        ),
                    },
                ],
            )
        except Exception as exc:
            _raise_provider_error("extract RKM draft", exc)

        content = response.choices[0].message.content
        if not content:
            raise AppError(
                "INTERNAL_ERROR",
                "AI provider returned an empty RKM extraction response",
                status_code=502,
            )
        try:
            payload = json.loads(content)
        except json.JSONDecodeError as exc:
            raise AppError(
                "INTERNAL_ERROR",
                "AI provider returned invalid JSON for RKM extraction",
                status_code=502,
            ) from exc

        result = normalize_rkm_extraction(payload)
        result["provider"] = "openai"
        result["model"] = self.model
        return result

    async def recommend_architecture(
        self,
        published_rkm: dict[str, Any],
        *,
        knowledge_pack_context: str = "",
    ) -> dict[str, Any]:
        system_prompt = _load_prompt("architecture_recommendation.txt")
        pack = knowledge_pack_context.strip()
        user_content = (
            "Create a vendor-neutral architecture recommendation from this "
            "Published Requirement Knowledge Model JSON:\n\n"
            + json.dumps(published_rkm, ensure_ascii=True)[:120000]
        )
        if pack:
            user_content += (
                "\n\nAdditional vendor-neutral knowledge pack guidance:\n" + pack[:8000]
            )
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                temperature=0.2,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],
            )
        except Exception as exc:
            _raise_provider_error("recommend architecture", exc)

        content = response.choices[0].message.content
        if not content:
            raise AppError(
                "INTERNAL_ERROR",
                "AI provider returned an empty architecture response",
                status_code=502,
            )
        try:
            payload = json.loads(content)
        except json.JSONDecodeError as exc:
            raise AppError(
                "INTERNAL_ERROR",
                "AI provider returned invalid JSON for architecture",
                status_code=502,
            ) from exc

        result = normalize_architecture(payload)
        result["provider"] = "openai"
        result["model"] = self.model
        return result

    async def recommend_architectures(
        self,
        published_rkm: dict[str, Any],
        *,
        domain_context: str = "",
        pattern_context: str = "",
    ) -> dict[str, Any]:
        system_prompt = _load_prompt("architecture_candidates.txt")
        user_content = (
            "Propose 1–3 vendor-neutral architecture candidates from this "
            "Published Requirement Knowledge Model JSON. Use only pattern codes "
            "from the pattern context and respect domain analysis context.\n\n"
            + json.dumps(published_rkm, ensure_ascii=True)[:120000]
        )
        domains = domain_context.strip()
        patterns = pattern_context.strip()
        if domains:
            user_content += "\n\nDomain analysis context:\n" + domains[:8000]
        if patterns:
            user_content += (
                "\n\nPhase 3 pattern catalog / pack context:\n" + patterns[:8000]
            )
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                temperature=0.2,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],
            )
        except Exception as exc:
            _raise_provider_error("recommend architecture candidates", exc)

        content = response.choices[0].message.content
        if not content:
            raise AppError(
                "INTERNAL_ERROR",
                "AI provider returned an empty architecture candidates response",
                status_code=502,
            )
        try:
            payload = json.loads(content)
        except json.JSONDecodeError as exc:
            raise AppError(
                "INTERNAL_ERROR",
                "AI provider returned invalid JSON for architecture candidates",
                status_code=502,
            ) from exc

        result = normalize_architecture_candidates(payload)
        result["provider"] = "openai"
        result["model"] = self.model
        return result

    async def identify_solution_domains(
        self,
        published_rkm: dict[str, Any],
        *,
        knowledge_pack_context: str = "",
    ) -> dict[str, Any]:
        system_prompt = _load_prompt("domain_identification.txt")
        pack = knowledge_pack_context.strip()
        user_content = (
            "Identify solution domains from this Published Requirement Knowledge "
            "Model JSON. Use only catalog domain codes from the knowledge pack "
            "context.\n\n"
            + json.dumps(published_rkm, ensure_ascii=True)[:120000]
        )
        if pack:
            user_content += (
                "\n\nPhase 3 domain knowledge pack / catalog context:\n" + pack[:8000]
            )
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                temperature=0.2,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],
            )
        except Exception as exc:
            _raise_provider_error("identify solution domains", exc)

        content = response.choices[0].message.content
        if not content:
            raise AppError(
                "INTERNAL_ERROR",
                "AI provider returned an empty domain identification response",
                status_code=502,
            )
        try:
            payload = json.loads(content)
        except json.JSONDecodeError as exc:
            raise AppError(
                "INTERNAL_ERROR",
                "AI provider returned invalid JSON for domain identification",
                status_code=502,
            ) from exc

        result = normalize_domain_identification(payload)
        result["provider"] = "openai"
        result["model"] = self.model
        return result

    async def generate_proposal_content(
        self,
        snapshot: dict[str, Any],
        content_plan: dict[str, Any],
        *,
        prompt_version: str = "proposal_v1",
    ) -> dict[str, Any]:
        system_prompt = _load_prompt("proposal_generate.txt")
        user_content = (
            "Generate a structured customer proposal from this immutable source "
            "snapshot and content plan. Never invent prices, warranties, SLAs, or "
            "dates. Mark gaps as review_required=true.\n\n"
            "SOURCE SNAPSHOT JSON:\n"
            + json.dumps(snapshot, ensure_ascii=True)[:100000]
            + "\n\nCONTENT PLAN JSON:\n"
            + json.dumps(content_plan, ensure_ascii=True)[:20000]
        )
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                temperature=0.2,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],
            )
        except Exception as exc:
            _raise_provider_error("generate proposal content", exc)

        content = response.choices[0].message.content
        if not content:
            raise AppError(
                "INTERNAL_ERROR",
                "AI provider returned an empty proposal response",
                status_code=502,
            )
        try:
            payload = json.loads(content)
        except json.JSONDecodeError as exc:
            raise AppError(
                "INTERNAL_ERROR",
                "AI provider returned invalid JSON for proposal content",
                status_code=502,
            ) from exc

        payload["provider"] = "openai"
        payload["model"] = self.model
        payload["prompt_version"] = prompt_version
        return payload

    async def generate_presentation_content(
        self,
        snapshot: dict[str, Any],
        content_plan: dict[str, Any],
        *,
        prompt_version: str = "presentation_v1",
    ) -> dict[str, Any]:
        system_prompt = _load_prompt("presentation_generate.txt")
        user_content = (
            "Generate a structured presentation from this immutable source "
            "snapshot and content plan. One key_message per slide. Never invent "
            "prices, warranties, SLAs, or dates.\n\n"
            "SOURCE SNAPSHOT JSON:\n"
            + json.dumps(snapshot, ensure_ascii=True)[:100000]
            + "\n\nCONTENT PLAN JSON:\n"
            + json.dumps(content_plan, ensure_ascii=True)[:20000]
        )
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                temperature=0.2,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],
            )
        except Exception as exc:
            _raise_provider_error("generate presentation content", exc)

        content = response.choices[0].message.content
        if not content:
            raise AppError(
                "INTERNAL_ERROR",
                "AI provider returned an empty presentation response",
                status_code=502,
            )
        try:
            payload = json.loads(content)
        except json.JSONDecodeError as exc:
            raise AppError(
                "INTERNAL_ERROR",
                "AI provider returned invalid JSON for presentation content",
                status_code=502,
            ) from exc

        payload["provider"] = "openai"
        payload["model"] = self.model
        payload["prompt_version"] = prompt_version
        return payload


def _raise_provider_error(action: str, exc: Exception) -> NoReturn:
    """Map OpenAI SDK errors to actionable API messages (never include secrets)."""
    logger.exception("OpenAI failed to %s", action)

    if isinstance(exc, AuthenticationError):
        raise AppError(
            "AI_AUTH_FAILED",
            "OpenAI authentication failed. Check that OPENAI_API_KEY is valid "
            "and recreate the backend container after updating .env.",
            status_code=502,
        ) from exc

    if isinstance(exc, RateLimitError):
        raise AppError(
            "AI_QUOTA_EXCEEDED",
            "OpenAI rate limit or quota exceeded. Check billing and usage limits "
            "at platform.openai.com.",
            status_code=502,
        ) from exc

    if isinstance(exc, APITimeoutError):
        raise AppError(
            "AI_UNAVAILABLE",
            "OpenAI request timed out. Please retry analysis.",
            status_code=502,
        ) from exc

    if isinstance(exc, APIConnectionError):
        raise AppError(
            "AI_UNAVAILABLE",
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
