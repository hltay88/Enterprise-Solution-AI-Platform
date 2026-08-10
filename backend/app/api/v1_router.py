"""Aggregate Phase 2 routers under /api/v1."""

from fastapi import APIRouter

from app.api.routes import (
    v1_agents,
    v1_architecture,
    v1_architectures,
    v1_audit,
    v1_bom,
    v1_deliverables,
    v1_documents,
    v1_domains,
    v1_gap,
    v1_knowledge,
    v1_packages,
    v1_requirements,
    v1_retrieval,
    v1_vendors,
)

v1_router = APIRouter()
v1_router.include_router(v1_documents.router)
v1_router.include_router(v1_requirements.router)
v1_router.include_router(v1_gap.router)
v1_router.include_router(v1_audit.router)
v1_router.include_router(v1_architecture.router)
v1_router.include_router(v1_architectures.router)
v1_router.include_router(v1_domains.router)
v1_router.include_router(v1_vendors.router)
v1_router.include_router(v1_bom.router)
v1_router.include_router(v1_deliverables.router)
v1_router.include_router(v1_packages.router)
v1_router.include_router(v1_knowledge.router)
v1_router.include_router(v1_retrieval.router)
v1_router.include_router(v1_agents.router)
