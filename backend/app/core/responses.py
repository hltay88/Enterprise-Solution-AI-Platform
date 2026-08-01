"""ATLAS-014 response envelope helpers."""

from typing import Any

from fastapi.responses import JSONResponse


def success_response(
    data: Any = None,
    message: str | None = None,
    status_code: int = 200,
) -> dict[str, Any] | JSONResponse:
    payload = {
        "success": True,
        "data": data,
        "message": message,
    }
    if status_code == 200:
        return payload
    return JSONResponse(status_code=status_code, content=payload)


def error_response(
    code: str,
    message: str,
    status_code: int,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "data": None,
            "error": {
                "code": code,
                "message": message,
            },
        },
    )
