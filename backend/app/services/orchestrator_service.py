"""Sprint 5.3 — Atlas orchestrator (advise-only multi-agent coordination)."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationAppError
from app.models.agent import Agent, AgentRun, AgentToolCall
from app.models.user import User
from app.repositories.project_repository import ProjectRepository
from app.schemas.agent import (
    AgentRunDetailOut,
    AgentRunRequest,
    AgentRunSummaryOut,
    AgentSummaryOut,
    AgentToolCallOut,
    OrchestratorConflict,
    SpecialistOutput,
)
from app.services.agent_tools import AgentToolGateway
from app.services.audit_service import AuditService
from app.services.specialist_agents import RUNNABLE_AGENTS, run_specialist


class OrchestratorService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.projects = ProjectRepository(db)
        self.audits = AuditService(db)

    def ensure_agents_seeded(self) -> None:
        """Upsert registry so promoted specialists flip runnable=true on existing DBs."""
        existing = {
            row.id: row for row in self.db.scalars(select(Agent)).all()
        }
        for agent_id, meta in RUNNABLE_AGENTS.items():
            description = meta.get("description") or f"{meta['name']} advisory agent"
            row = existing.get(agent_id)
            if row is None:
                self.db.add(
                    Agent(
                        id=agent_id,
                        name=meta["name"],
                        domain_code=meta["domain_code"],
                        description=description,
                        enabled=True,
                        runnable=True,
                        version="1.0.0",
                    ),
                )
            else:
                row.name = meta["name"]
                row.domain_code = meta["domain_code"]
                row.description = description
                row.enabled = True
                row.runnable = True
                row.version = "1.0.0"
        self.db.commit()

    def list_agents(self) -> list[AgentSummaryOut]:
        self.ensure_agents_seeded()
        rows = list(self.db.scalars(select(Agent).order_by(Agent.id.asc())).all())
        return [
            AgentSummaryOut(
                id=row.id,
                name=row.name,
                domain_code=row.domain_code,
                description=row.description,
                enabled=row.enabled,
                runnable=row.runnable,
                version=row.version,
            )
            for row in rows
            if row.enabled
        ]

    def list_runs(self, project_id: UUID, user_id: UUID) -> list[AgentRunSummaryOut]:
        if self.projects.get_for_user(project_id, user_id) is None:
            raise NotFoundError("Project not found")
        rows = list(
            self.db.scalars(
                select(AgentRun)
                .where(AgentRun.project_id == project_id)
                .order_by(AgentRun.created_at.desc())
                .limit(50),
            ).all(),
        )
        return [self._to_summary(row) for row in rows]

    def get_run(self, run_id: UUID, user_id: UUID) -> AgentRunDetailOut:
        row = self.db.get(AgentRun, run_id)
        if row is None:
            raise NotFoundError("Agent run not found")
        if self.projects.get_for_user(row.project_id, user_id) is None:
            raise NotFoundError("Agent run not found")
        return self._to_detail(row)

    def run(self, project_id: UUID, user: User, body: AgentRunRequest | None = None) -> AgentRunDetailOut:
        if self.projects.get_for_user(project_id, user.id) is None:
            raise NotFoundError("Project not found")
        body = body or AgentRunRequest()
        self.ensure_agents_seeded()

        selected = self._select_agents(body)
        if not selected:
            raise ValidationAppError("No runnable agents selected for this run")

        now = datetime.now(timezone.utc)
        run = AgentRun(
            project_id=project_id,
            status="running",
            goal=body.goal,
            focus_domains=list(body.focus_domains or selected),
            input_json=body.model_dump(mode="json"),
            output_json={},
            created_by=user.id,
            started_at=now,
        )
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)

        tools = AgentToolGateway(
            self.db,
            project_id=project_id,
            user=user,
            run_id=run.id,
            agent_id="orchestrator",
        )
        # Baseline project read for the orchestrator context
        try:
            tools.call("get_project", {})
        except Exception:
            pass

        specialists: list[SpecialistOutput] = []
        try:
            for agent_id in selected:
                try:
                    specialists.append(run_specialist(agent_id, tools, goal=body.goal))
                except Exception as agent_exc:
                    specialists.append(
                        SpecialistOutput(
                            agent_id=agent_id,
                            domain_code=RUNNABLE_AGENTS[agent_id]["domain_code"],
                            status="blocked",
                            summary=f"{agent_id} specialist failed: {agent_exc}",
                            confidence=0.0,
                            risks=[str(agent_exc)],
                        ),
                    )

            conflicts = self._merge_conflicts(specialists)
            overall = (
                sum(s.confidence for s in specialists) / len(specialists) if specialists else 0.0
            )
            review_required = any(
                s.status in {"insufficient_evidence", "blocked"} for s in specialists
            ) or len(conflicts) > 0

            output = {
                "mode": "advise_only",
                "specialists": [s.model_dump(mode="json") for s in specialists],
                "conflicts": [c.model_dump(mode="json") for c in conflicts],
                "overall_confidence": overall,
                "review_required": review_required,
                "note": "Agents cannot approve customer-facing outputs.",
            }
            run.status = "completed"
            run.output_json = output
            run.overall_confidence = overall
            run.conflict_count = len(conflicts)
            run.completed_at = datetime.now(timezone.utc)
            run.updated_at = run.completed_at
            self.audits.record(
                project_id=project_id,
                user_id=user.id,
                action="agent.run.completed",
                summary=f"Orchestrator completed with {len(specialists)} specialists",
                resource_type="agent_run",
                resource_id=run.id,
                metadata={"agents": selected, "conflicts": len(conflicts)},
                commit=False,
            )
            self.db.commit()
        except Exception as exc:
            run.status = "failed"
            run.error = str(exc)
            run.completed_at = datetime.now(timezone.utc)
            run.updated_at = run.completed_at
            self.db.commit()
            raise

        return self._to_detail(run)

    @staticmethod
    def _select_agents(body: AgentRunRequest) -> list[str]:
        if body.include_agents:
            return [a for a in body.include_agents if a in RUNNABLE_AGENTS]
        if body.focus_domains:
            selected = []
            for agent_id, meta in RUNNABLE_AGENTS.items():
                if meta["domain_code"] in body.focus_domains or agent_id in body.focus_domains:
                    selected.append(agent_id)
            return selected
        return list(RUNNABLE_AGENTS.keys())

    @staticmethod
    def _merge_conflicts(specialists: list[SpecialistOutput]) -> list[OrchestratorConflict]:
        conflicts: list[OrchestratorConflict] = []
        seen: set[str] = set()
        for specialist in specialists:
            for text in specialist.conflicts:
                key = text.strip().lower()
                if not key or key in seen:
                    continue
                seen.add(key)
                conflicts.append(
                    OrchestratorConflict(
                        code=f"conflict_{len(conflicts)+1}",
                        summary=text,
                        agents=[specialist.agent_id],
                        severity="warning",
                    ),
                )

        # Cross-agent presence conflicts
        ids = {s.agent_id for s in specialists}
        pairs = [
            ("security", "cloud", "security_cloud",
             "Security and Cloud both active — reconcile shared responsibility and exposure paths."),
            ("wireless", "security", "wireless_security",
             "Wireless and Security both active — reconcile SSID isolation / NAC requirements."),
            ("storage", "backup", "storage_backup",
             "Storage and Backup both active — reconcile snapshot vs backup ownership and retention."),
            ("backup", "cloud", "backup_cloud",
             "Backup and Cloud both active — reconcile immutable copies and recovery regions."),
            ("data_centre", "cloud", "dc_cloud",
             "Data Centre and Cloud both active — reconcile hybrid placement and interconnect."),
            ("smart_building", "security", "sb_security",
             "Smart Building and Security both active — reconcile OT/IT segmentation."),
            ("av", "networking", "av_networking",
             "AV and Networking both active — reconcile QoS / VLAN design for media."),
            ("led_videowall", "av", "led_av",
             "LED and AV both active — reconcile control systems and content workflow."),
            ("compute", "storage", "compute_storage",
             "Compute and Storage both active — reconcile attachment model and IOPS/HA domains."),
            ("hci", "compute", "hci_compute",
             "HCI and Compute both active — reconcile HCI vs discrete compute placement."),
            ("hci", "storage", "hci_storage",
             "HCI and Storage both active — reconcile HCI vs discrete storage ownership."),
            ("hci", "backup", "hci_backup",
             "HCI and Backup both active — reconcile native snapshots vs external backup."),
            ("digital_signage", "networking", "signage_networking",
             "Digital Signage and Networking both active — reconcile VLAN/bandwidth for players."),
            ("billboard", "led_videowall", "billboard_led",
             "Billboard and LED both active — reconcile outdoor vs indoor display standards."),
            ("billboard", "digital_signage", "billboard_signage",
             "Billboard and Digital Signage both active — reconcile CMS/player ownership."),
            ("iot", "security", "iot_security",
             "IoT and Security both active — reconcile device identity and OT segmentation."),
            ("iot", "smart_building", "iot_smart_building",
             "IoT and Smart Building both active — reconcile edge/BMS platform ownership."),
        ]
        for left, right, code, msg in pairs:
            if left in ids and right in ids and msg.lower() not in seen:
                seen.add(msg.lower())
                conflicts.append(
                    OrchestratorConflict(
                        code=code,
                        summary=msg,
                        agents=[left, right],
                        severity="warning",
                    ),
                )
        return conflicts

    def _to_summary(self, row: AgentRun) -> AgentRunSummaryOut:
        return AgentRunSummaryOut(
            id=row.id,
            project_id=row.project_id,
            status=row.status,
            goal=row.goal,
            focus_domains=list(row.focus_domains or []),
            overall_confidence=row.overall_confidence,
            conflict_count=row.conflict_count,
            created_at=row.created_at,
            completed_at=row.completed_at,
        )

    def _to_detail(self, row: AgentRun) -> AgentRunDetailOut:
        output = row.output_json if isinstance(row.output_json, dict) else {}
        specialists = [
            SpecialistOutput.model_validate(item)
            for item in (output.get("specialists") or [])
        ]
        conflicts = [
            OrchestratorConflict.model_validate(item)
            for item in (output.get("conflicts") or [])
        ]
        tool_rows = list(
            self.db.scalars(
                select(AgentToolCall)
                .where(AgentToolCall.agent_run_id == row.id)
                .order_by(AgentToolCall.created_at.asc()),
            ).all(),
        )
        return AgentRunDetailOut(
            **self._to_summary(row).model_dump(),
            input=row.input_json if isinstance(row.input_json, dict) else {},
            output=output,
            specialists=specialists,
            conflicts=conflicts,
            tool_calls=[
                AgentToolCallOut(
                    id=t.id,
                    agent_id=t.agent_id,
                    tool_name=t.tool_name,
                    ok=t.ok,
                    error=t.error,
                    latency_ms=t.latency_ms,
                    created_at=t.created_at,
                )
                for t in tool_rows
            ],
            error=row.error,
            review_required=bool(output.get("review_required")),
        )
