"""AI provider configuration and connectivity diagnostics."""

from fastapi import APIRouter

from app.api.deps import CurrentUser
from app.ai.openai_provider import probe_openai_connection
from app.core.config import settings
from app.core.responses import success_response

router = APIRouter(prefix="/ai", tags=["ai"])


@router.get("/status")
async def get_ai_status(_: CurrentUser) -> dict:
    """Return whether OpenAI is configured and whether a live probe succeeds."""
    key = settings.openai_api_key
    configured = bool(key)
    payload: dict = {
        "provider": "openai",
        "configured": configured,
        "model": settings.openai_model,
        "key_prefix": f"{key[:7]}..." if key and len(key) >= 7 else None,
        "key_length": len(key) if key else 0,
        "reachable": False,
        "detail": "OPENAI_API_KEY is not configured" if not configured else None,
    }

    if not configured:
        return success_response(data=payload)

    try:
        await probe_openai_connection()
        payload["reachable"] = True
        payload["detail"] = "OpenAI API key accepted"
    except Exception as exc:  # noqa: BLE001 - surface mapped AppError message
        message = getattr(exc, "message", None) or str(exc)
        payload["reachable"] = False
        payload["detail"] = message

    return success_response(data=payload)
