"""Specialist structured completion — local always, optional cloud when configured.

Keeps Mac demos offline-capable while completing Phase 5 AI path requirements.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from app.core.config import settings
from app.schemas.agent import SpecialistFinding, SpecialistOutput

logger = logging.getLogger(__name__)


def enrich_specialist_output(base: SpecialistOutput, *, context: dict[str, Any]) -> SpecialistOutput:
    """Optionally refine narrative fields using a lightweight local NLP pass.

    Cloud LLM enrichment runs only when ATLAS_AI_PROVIDER is gemini/openai and keys exist;
    failures fall back to the heuristic base unchanged.
    """
    provider = (settings.atlas_ai_provider or "auto").lower()
    if provider in {"gemini", "openai", "auto"}:
        try:
            refined = _try_cloud_refine(base, context=context)
            if refined is not None:
                return refined
        except Exception:
            logger.debug("specialist cloud refine skipped", exc_info=True)

    return _local_refine(base, context=context)


def _local_refine(base: SpecialistOutput, *, context: dict[str, Any]) -> SpecialistOutput:
    """Deterministic local enrichment — no network."""
    goal = str(context.get("goal") or "").strip()
    rkm_summary = str(context.get("rkm_summary") or "").strip()
    hit_count = int(context.get("hit_count") or 0)

    findings = list(base.findings)
    if hit_count > 0 and not any(f.code == "evidence_density" for f in findings):
        findings.append(
            SpecialistFinding(
                code="evidence_density",
                statement=f"Retrieved {hit_count} knowledge chunk(s) for grounding.",
                severity="info",
            ),
        )
    if goal and not any(f.code == "goal_aligned" for f in findings):
        findings.append(
            SpecialistFinding(
                code="goal_aligned",
                statement=f"Assessment scoped to goal: {goal[:200]}",
                severity="info",
            ),
        )

    summary = base.summary
    if rkm_summary and "RKM" not in summary:
        summary = f"{summary} Context: {rkm_summary[:160]}"

    # Confidence slight uplift when evidence+goal present
    confidence = base.confidence
    if hit_count > 0 and goal:
        confidence = min(1.0, confidence + 0.05)

    return base.model_copy(
        update={
            "findings": findings,
            "summary": summary[:800],
            "confidence": confidence,
            "tools_used": list(base.tools_used) + (["local_refine"] if "local_refine" not in base.tools_used else []),
        },
    )


def _try_cloud_refine(base: SpecialistOutput, *, context: dict[str, Any]) -> SpecialistOutput | None:
    """Best-effort: only if a cloud key is configured; sync-friendly no-op otherwise."""
    has_gemini = bool(settings.effective_gemini_api_key)
    has_openai = bool(settings.openai_api_key)
    mode = (settings.atlas_ai_provider or "auto").lower()
    if mode == "local":
        return None
    if mode == "gemini" and not has_gemini:
        return None
    if mode == "openai" and not has_openai:
        return None
    if mode == "auto" and not (has_gemini or has_openai):
        return None

    # Avoid blocking Mac CI: if keys present we still keep output schema-safe by
    # applying a structured local paraphrase rather than a live network call in tests.
    # Live enrichment can be enabled explicitly via ATLAS_SPECIALIST_LLM=1.
    if not getattr(settings, "atlas_specialist_llm", False):
        return _local_refine(base, context=context)

    prompt = {
        "agent_id": base.agent_id,
        "domain": base.domain_code,
        "base_summary": base.summary,
        "goal": context.get("goal"),
        "findings": [f.model_dump() for f in base.findings[:8]],
    }
    text = _cloud_json_completion(json.dumps(prompt))
    if not text:
        return None
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        # Accept fenced JSON
        match = re.search(r"\{.*\}", text, re.S)
        if not match:
            return None
        data = json.loads(match.group(0))

    summary = str(data.get("summary") or base.summary)[:800]
    recommendations = [str(x) for x in (data.get("recommendations") or base.recommendations)][:8]
    risks = [str(x) for x in (data.get("risks") or base.risks)][:8]
    return base.model_copy(
        update={
            "summary": summary,
            "recommendations": recommendations or base.recommendations,
            "risks": risks or base.risks,
            "tools_used": list(base.tools_used) + ["llm_refine"],
        },
    )


def _cloud_json_completion(prompt: str) -> str | None:
    """Minimal optional cloud call; returns None on any failure."""
    try:
        if settings.effective_gemini_api_key and (settings.atlas_ai_provider in {"auto", "gemini"}):
            from google import genai

            client = genai.Client(api_key=settings.effective_gemini_api_key)
            resp = client.models.generate_content(
                model=settings.gemini_model,
                contents=(
                    "Return ONLY JSON with keys summary, recommendations[], risks[]. "
                    f"Input: {prompt[:6000]}"
                ),
            )
            return getattr(resp, "text", None)
        if settings.openai_api_key and settings.atlas_ai_provider in {"auto", "openai"}:
            from openai import OpenAI

            client = OpenAI(api_key=settings.openai_api_key)
            resp = client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": "Return ONLY JSON with keys summary, recommendations[], risks[].",
                    },
                    {"role": "user", "content": prompt[:6000]},
                ],
                temperature=0.2,
            )
            return resp.choices[0].message.content
    except Exception:
        logger.debug("cloud specialist completion failed", exc_info=True)
    return None
