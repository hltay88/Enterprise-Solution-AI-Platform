"""Sprint 5.2 — Retrieval APIs under /api/v1/retrieval."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.core.responses import success_response
from app.schemas.retrieval import RetrievalSearchIn
from app.services.retrieval_service import RetrievalService

router = APIRouter(prefix="/retrieval", tags=["v1-retrieval"])


@router.post("/search")
def retrieval_search(
    body: RetrievalSearchIn,
    current_user: CurrentUser,
    db: DbSession,
) -> dict:
    result = RetrievalService(db).search(body, current_user)
    return success_response(data=result.model_dump(mode="json"))


@router.post("/context")
def retrieval_context(
    body: RetrievalSearchIn,
    current_user: CurrentUser,
    db: DbSession,
) -> dict:
    result = RetrievalService(db).context(body, current_user)
    payload = result.model_dump(mode="json")
    if result.insufficient_evidence:
        payload["message"] = "INSUFFICIENT EVIDENCE — REVIEW REQUIRED"
    return success_response(data=payload)
