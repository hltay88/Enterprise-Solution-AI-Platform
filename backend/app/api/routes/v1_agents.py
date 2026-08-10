"""Sprint 5.3 — Multi-agent orchestration APIs under /api/v1."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession, EditorUser
from app.core.responses import success_response
from app.schemas.agent import AgentRunRequest
from app.services.orchestrator_service import OrchestratorService

router = APIRouter(tags=["v1-agents"])


@router.get("/agents")
def list_agents(
    current_user: CurrentUser,
    db: DbSession,
) -> dict:
    _ = current_user
    agents = OrchestratorService(db).list_agents()
    return success_response(data=[a.model_dump(mode="json") for a in agents])


@router.post("/projects/{project_id}/agent-runs")
def create_agent_run(
    project_id: UUID,
    body: AgentRunRequest,
    current_user: EditorUser,
    db: DbSession,
) -> dict:
    result = OrchestratorService(db).run(project_id, current_user, body)
    return success_response(data=result.model_dump(mode="json"), status_code=201)


@router.get("/projects/{project_id}/agent-runs")
def list_agent_runs(
    project_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> dict:
    rows = OrchestratorService(db).list_runs(project_id, current_user.id)
    return success_response(data=[r.model_dump(mode="json") for r in rows])


@router.get("/agent-runs/{run_id}")
def get_agent_run(
    run_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> dict:
    result = OrchestratorService(db).get_run(run_id, current_user.id)
    return success_response(data=result.model_dump(mode="json"))
