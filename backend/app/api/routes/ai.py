"""AI provider configuration and connectivity diagnostics."""

from fastapi import APIRouter

from app.api.deps import CurrentUser
from app.ai.gemini_provider import probe_gemini_connection
from app.ai.openai_provider import probe_openai_connection
from app.core.config import settings
from app.core.responses import success_response

router = APIRouter(prefix="/ai", tags=["ai"])


def _key_prefix(key: str | None) -> str | None:
    if not key or len(key) < 4:
        return None
    return f"{key[:4]}..."


@router.get("/status")
async def get_ai_status(_: CurrentUser) -> dict:
    """Return provider mode and whether Gemini/OpenAI are usable."""
    mode = settings.atlas_ai_provider
    gemini_key = settings.effective_gemini_api_key
    openai_key = settings.openai_api_key
    fallback_enabled = mode in {"auto", "local"}

    payload: dict = {
        "provider": mode,
        "configured": bool(gemini_key or openai_key) or mode == "local",
        "model": settings.gemini_model if gemini_key else settings.openai_model,
        "key_prefix": _key_prefix(gemini_key) or _key_prefix(openai_key),
        "key_length": len(gemini_key or openai_key or ""),
        "reachable": False,
        "fallback_enabled": fallback_enabled,
        "gemini_configured": bool(gemini_key),
        "openai_configured": bool(openai_key),
        "detail": None,
    }

    if mode == "local":
        payload["reachable"] = True
        payload["model"] = "local"
        payload["detail"] = "Using local analysis provider (no cloud AI call)."
        return success_response(data=payload)

    if mode == "gemini":
        return success_response(data=await _status_for_gemini(payload, require=True))

    if mode == "openai":
        return success_response(data=await _status_for_openai(payload, require=True))

    # auto
    details: list[str] = []
    reachable = False

    if gemini_key:
        gemini_payload = await _status_for_gemini(dict(payload), require=False)
        details.append(gemini_payload["detail"])
        reachable = reachable or bool(gemini_payload["reachable"])
        if gemini_payload["reachable"]:
            payload["model"] = settings.gemini_model
            payload["key_prefix"] = _key_prefix(gemini_key)
    else:
        details.append("GEMINI_API_KEY not set.")

    if openai_key:
        openai_payload = await _status_for_openai(dict(payload), require=False)
        details.append(openai_payload["detail"])
        reachable = reachable or bool(openai_payload["reachable"])
        if not gemini_key and openai_payload["reachable"]:
            payload["model"] = settings.openai_model
            payload["key_prefix"] = _key_prefix(openai_key)
    else:
        details.append("OPENAI_API_KEY not set.")

    if fallback_enabled:
        details.append("Local fallback is enabled.")
        reachable = True

    payload["reachable"] = reachable
    payload["detail"] = " ".join(item for item in details if item)
    return success_response(data=payload)


async def _status_for_gemini(payload: dict, *, require: bool) -> dict:
    key = settings.effective_gemini_api_key
    payload["model"] = settings.gemini_model
    payload["key_prefix"] = _key_prefix(key)
    payload["key_length"] = len(key or "")
    if not key:
        payload["reachable"] = False
        payload["detail"] = "GEMINI_API_KEY is not configured."
        if not require:
            return payload
        return payload

    try:
        await probe_gemini_connection()
        payload["reachable"] = True
        payload["detail"] = (
            f"Gemini ready ({settings.gemini_model}, {payload['key_prefix']})."
        )
    except Exception as exc:  # noqa: BLE001
        message = getattr(exc, "message", None) or str(exc)
        payload["reachable"] = False
        payload["detail"] = message
    return payload


async def _status_for_openai(payload: dict, *, require: bool) -> dict:
    key = settings.openai_api_key
    payload["model"] = settings.openai_model
    payload["key_prefix"] = _key_prefix(key)
    payload["key_length"] = len(key or "")
    if not key:
        payload["reachable"] = False
        payload["detail"] = "OPENAI_API_KEY is not configured."
        return payload

    try:
        await probe_openai_connection()
        payload["reachable"] = True
        payload["detail"] = (
            f"OpenAI ready ({settings.openai_model}, {payload['key_prefix']})."
        )
    except Exception as exc:  # noqa: BLE001
        message = getattr(exc, "message", None) or str(exc)
        payload["reachable"] = False
        payload["detail"] = message
    return payload
