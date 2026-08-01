"""AI provider configuration and connectivity diagnostics."""

from fastapi import APIRouter

from app.api.deps import CurrentUser
from app.ai.openai_provider import probe_openai_connection
from app.core.config import settings
from app.core.responses import success_response

router = APIRouter(prefix="/ai", tags=["ai"])


@router.get("/status")
async def get_ai_status(_: CurrentUser) -> dict:
    """Return provider mode and whether OpenAI is usable."""
    mode = settings.atlas_ai_provider
    key = settings.openai_api_key
    configured = bool(key)
    fallback_enabled = mode in {"auto", "local"}

    payload: dict = {
        "provider": mode,
        "configured": configured,
        "model": settings.openai_model,
        "key_prefix": f"{key[:7]}..." if key and len(key) >= 7 else None,
        "key_length": len(key) if key else 0,
        "reachable": False,
        "fallback_enabled": fallback_enabled,
        "detail": None,
    }

    if mode == "local":
        payload["reachable"] = True
        payload["detail"] = "Using local analysis provider (no OpenAI call)."
        return success_response(data=payload)

    if not configured:
        payload["detail"] = (
            "OPENAI_API_KEY is not configured. "
            + (
                "Local fallback will be used for analysis."
                if fallback_enabled
                else "Set OPENAI_API_KEY to run analysis."
            )
        )
        payload["reachable"] = fallback_enabled
        return success_response(data=payload)

    try:
        await probe_openai_connection()
        payload["reachable"] = True
        if fallback_enabled:
            payload["detail"] = (
                f"OpenAI ready ({settings.openai_model}, {payload['key_prefix']}). "
                "Local fallback is enabled if quota is exceeded."
            )
        else:
            payload["detail"] = (
                f"OpenAI ready ({settings.openai_model}, {payload['key_prefix']})."
            )
    except Exception as exc:  # noqa: BLE001 - surface mapped AppError message
        message = getattr(exc, "message", None) or str(exc)
        payload["reachable"] = fallback_enabled
        if fallback_enabled:
            payload["detail"] = f"{message} Local fallback is enabled."
        else:
            payload["detail"] = message

    return success_response(data=payload)
