"""Aggregate API routers under /api."""

from fastapi import APIRouter

from app.api.routes import analysis, auth, clarifications, documents, health, projects

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(projects.router)
api_router.include_router(documents.router)
api_router.include_router(analysis.router)
api_router.include_router(clarifications.router)
