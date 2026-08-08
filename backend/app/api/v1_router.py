"""Aggregate Phase 2 routers under /api/v1."""

from fastapi import APIRouter

from app.api.routes import v1_documents, v1_gap, v1_requirements

v1_router = APIRouter()
v1_router.include_router(v1_documents.router)
v1_router.include_router(v1_requirements.router)
v1_router.include_router(v1_gap.router)
