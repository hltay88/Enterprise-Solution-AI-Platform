"""Sprint 5.3 — read-only agent tools with audit trail."""

from __future__ import annotations

import time
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenError, NotFoundError, ValidationAppError
from app.models.agent import AgentToolCall
from app.models.user import User
from app.repositories.architecture_option_repository import ArchitectureOptionRepository
from app.repositories.domain_repository import DomainRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.rkm_repository import RkmRepository
from app.schemas.retrieval import RetrievalSearchIn
from app.services.audit_service import AuditService
from app.services.retrieval_service import RetrievalService
from app.services.vendor_catalogue_service import VendorCatalogueService

ALLOWED_TOOLS = frozenset(
    {
        "knowledge_search",
        "get_project",
        "get_published_rkm",
        "get_domain_analysis",
        "get_architectures",
        "search_vendor_catalogue",
    }
)

WRITE_TOOLS_DENIED = frozenset(
    {
        "approve_rkm",
        "publish_rkm",
        "generate_architecture",
        "import_bom",
        "approve_document",
        "update_rkm",
        "write_architecture",
    }
)


class AgentToolGateway:
    """Least-privilege tool gateway for specialist agents (read-only)."""

    def __init__(
        self,
        db: Session,
        *,
        project_id: UUID,
        user: User,
        run_id: UUID,
        agent_id: str | None = None,
    ) -> None:
        self.db = db
        self.project_id = project_id
        self.user = user
        self.run_id = run_id
        self.agent_id = agent_id
        self.projects = ProjectRepository(db)
        self.rkms = RkmRepository(db)
        self.domains = DomainRepository(db)
        self.architectures = ArchitectureOptionRepository(db)
        self.audits = AuditService(db)

    def call(self, tool_name: str, request: dict[str, Any] | None = None) -> dict[str, Any]:
        request = dict(request or {})
        if tool_name in WRITE_TOOLS_DENIED:
            raise ForbiddenError(f"Agent tool '{tool_name}' is not permitted (write denied)")
        if tool_name not in ALLOWED_TOOLS:
            raise ValidationAppError(f"Unknown agent tool: {tool_name}")

        started = time.perf_counter()
        ok = True
        error: str | None = None
        response: dict[str, Any] = {}
        try:
            handler = getattr(self, f"_tool_{tool_name}")
            response = handler(request)
            return response
        except Exception as exc:
            ok = False
            error = str(exc)
            response = {"error": error}
            raise
        finally:
            latency = int((time.perf_counter() - started) * 1000)
            self.db.add(
                AgentToolCall(
                    agent_run_id=self.run_id,
                    agent_id=self.agent_id,
                    tool_name=tool_name,
                    request_json=request,
                    response_json=_truncate_json(response),
                    ok=ok,
                    error=error,
                    latency_ms=latency,
                ),
            )
            try:
                self.audits.record(
                    project_id=self.project_id,
                    user_id=self.user.id,
                    action=f"agent.tool.{tool_name}",
                    summary=f"Agent tool {tool_name}" + (" failed" if not ok else ""),
                    resource_type="agent_run",
                    resource_id=self.run_id,
                    metadata={"agent_id": self.agent_id, "ok": ok, "latency_ms": latency},
                    commit=False,
                )
            except Exception:
                pass
            self.db.flush()

    def for_agent(self, agent_id: str) -> AgentToolGateway:
        clone = AgentToolGateway(
            self.db,
            project_id=self.project_id,
            user=self.user,
            run_id=self.run_id,
            agent_id=agent_id,
        )
        return clone

    def _require_project(self):
        project = self.projects.get_for_user(self.project_id, self.user.id)
        if project is None:
            raise NotFoundError("Project not found")
        return project

    def _tool_knowledge_search(self, request: dict[str, Any]) -> dict[str, Any]:
        self._require_project()
        query = (request.get("query") or "").strip()
        if not query:
            raise ValidationAppError("query is required")
        body = RetrievalSearchIn(
            query=query,
            domain_code=request.get("domain_code"),
            top_k=int(request.get("top_k") or 5),
            min_score=float(request.get("min_score") if request.get("min_score") is not None else 0.0),
        )
        result = RetrievalService(self.db).search(body, self.user)
        return result.model_dump(mode="json")

    def _tool_get_project(self, request: dict[str, Any]) -> dict[str, Any]:
        _ = request
        project = self._require_project()
        return {
            "id": str(project.id),
            "project_name": project.project_name,
            "customer": project.customer,
            "status": project.status,
            "request_type": getattr(project, "request_type", None),
        }

    def _tool_get_published_rkm(self, request: dict[str, Any]) -> dict[str, Any]:
        _ = request
        self._require_project()
        row = self.rkms.get_published(self.project_id)
        if row is None:
            return {"found": False, "rkm": None}
        payload = row.payload_json if isinstance(row.payload_json, dict) else {}
        return {
            "found": True,
            "rkm_id": str(row.id),
            "version_label": row.version_label,
            "status": row.status,
            "summary": str(
                payload.get("executive_summary")
                or payload.get("summary")
                or payload.get("project_overview")
                or "",
            )[:2000],
            "payload_excerpt": {
                k: payload.get(k)
                for k in (
                    "project_overview",
                    "business_objectives",
                    "constraints",
                    "non_functional_requirements",
                )
                if k in payload
            },
        }

    def _tool_get_domain_analysis(self, request: dict[str, Any]) -> dict[str, Any]:
        _ = request
        self._require_project()
        analysis = self.domains.get_latest(self.project_id)
        if analysis is None:
            return {"found": False, "domains": []}
        domains = self.domains.list_domains(analysis.id)
        return {
            "found": True,
            "analysis_id": str(analysis.id),
            "version_label": getattr(analysis, "version_label", None),
            "domains": [
                {
                    "code": getattr(d, "domain_code", None) or getattr(d, "code", None),
                    "name": getattr(d, "name", None) or getattr(d, "display_name", None),
                    "confidence": getattr(d, "confidence", None),
                }
                for d in domains
            ],
        }

    def _tool_get_architectures(self, request: dict[str, Any]) -> dict[str, Any]:
        _ = request
        self._require_project()
        rows = self.architectures.list_for_project(self.project_id)
        return {
            "count": len(rows),
            "architectures": [
                {
                    "id": str(row.id),
                    "title": getattr(row, "title", None) or getattr(row, "name", None),
                    "status": row.status,
                    "version_label": getattr(row, "version_label", None),
                    "summary": (getattr(row, "summary", None) or "")[:500],
                }
                for row in rows[:10]
            ],
        }

    def _tool_search_vendor_catalogue(self, request: dict[str, Any]) -> dict[str, Any]:
        self._require_project()
        q = (request.get("query") or "").strip()
        if not q:
            raise ValidationAppError("query is required")
        result = VendorCatalogueService(self.db).search(
            query=q,
            limit=int(request.get("limit") or 5),
        )
        return result.model_dump(mode="json")


def _truncate_json(payload: dict[str, Any], *, limit: int = 8000) -> dict[str, Any]:
    text = str(payload)
    if len(text) <= limit:
        return payload
    return {"truncated": True, "preview": text[:limit]}
