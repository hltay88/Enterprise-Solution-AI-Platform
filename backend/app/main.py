"""FastAPI application entrypoint for Project Atlas."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core.config import settings
from app.core.exceptions import AppError
from app.core.responses import error_response
from app.db.schema import ensure_schema
from app.db.session import SessionLocal
from app.services.auth_service import ensure_demo_user

# Register ORM models with SQLAlchemy metadata.
from app import models as _models  # noqa: F401

logger = logging.getLogger(__name__)


def _prepare_database() -> None:
    try:
        ensure_schema()
    except Exception:
        logger.exception("Could not apply schema upgrades")
        return

    db = SessionLocal()
    try:
        ensure_demo_user(
            db,
            name=settings.demo_user_name,
            email=settings.demo_user_email,
            password=settings.demo_user_password,
        )
        logger.info("Demo user ready: %s", settings.demo_user_email)
    except Exception:
        logger.exception("Could not seed demo user (database may be unavailable)")
    finally:
        db.close()


def _log_ai_config() -> None:
    logger.info("AI provider mode: %s", settings.atlas_ai_provider)
    gemini_key = settings.effective_gemini_api_key
    if gemini_key:
        logger.info(
            "Gemini configured: model=%s key_prefix=%s key_length=%d",
            settings.gemini_model,
            f"{gemini_key[:4]}...",
            len(gemini_key),
        )
    else:
        logger.info("GEMINI_API_KEY is not set")

    openai_key = settings.openai_api_key
    if openai_key:
        logger.info(
            "OpenAI configured: model=%s key_prefix=%s key_length=%d",
            settings.openai_model,
            f"{openai_key[:7]}...",
            len(openai_key),
        )
    else:
        logger.info("OPENAI_API_KEY is not set")

    if not gemini_key and not openai_key and settings.atlas_ai_provider != "local":
        logger.warning(
            "No cloud AI key configured — auto mode will use local analysis fallback",
        )


@asynccontextmanager
async def lifespan(_: FastAPI):
    _prepare_database()
    _log_ai_config()
    yield


def create_app() -> FastAPI:
    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        lifespan=lifespan,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(api_router, prefix="/api")

    @application.exception_handler(AppError)
    async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
        return error_response(exc.code, exc.message, exc.status_code)

    @application.exception_handler(RequestValidationError)
    async def validation_error_handler(
        _: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        return error_response(
            "VALIDATION_ERROR",
            str(exc.errors()),
            status_code=422,
        )

    @application.exception_handler(Exception)
    async def unhandled_error_handler(_: Request, __: Exception) -> JSONResponse:
        return error_response(
            "INTERNAL_ERROR",
            "An unexpected error occurred.",
            status_code=500,
        )

    return application


app = create_app()
