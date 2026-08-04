"""Aggregate Phase 2 routers under /api/v1."""

from fastapi import APIRouter

from app.api.routes import v1_documents

v1_router = APIRouter()
v1_router.include_router(v1_documents.router)
