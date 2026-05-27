from __future__ import annotations

from collections import Counter
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.business.models import AgentActionLog, BusinessArtifact, Engagement
from app.domains.business.repository import ArtifactRepository, EngagementRepository
from app.domains.business.schemas import (
    ArtifactCreate,
    ArtifactUpdate,
    EngagementCreate,
    EngagementUpdate,
    PipelineSummary,
)
from app.shared.base_service import BaseService
from app.shared.exceptions import ValidationError


class EngagementService(BaseService[Engagement]):
    async def create_from_schema(self, data: EngagementCreate) -> Engagement:
        _validate_stage(data.stage)
        instance = Engagement(**data.model_dump())
        return await self.repository.create(instance)

    async def update_from_schema(
        self, instance: Engagement, data: EngagementUpdate
    ) -> Engagement:
        values = data.model_dump(exclude_unset=True)
        if "stage" in values:
            _validate_stage(values["stage"])
        for field, value in values.items():
            setattr(instance, field, value)
        return await self.repository.update(instance)


class ArtifactService(BaseService[BusinessArtifact]):
    async def create_from_schema(self, data: ArtifactCreate) -> BusinessArtifact:
        instance = BusinessArtifact(**data.model_dump())
        return await self.repository.create(instance)

    async def update_from_schema(
        self, instance: BusinessArtifact, data: ArtifactUpdate
    ) -> BusinessArtifact:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(instance, field, value)
        return await self.repository.update(instance)


class BusinessReadService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def summarize_pipeline(self) -> PipelineSummary:
        engagements = (
            await self.session.execute(select(Engagement))
        ).scalars().all()
        artifacts = (
            await self.session.execute(select(BusinessArtifact))
        ).scalars().all()

        stage_counts = Counter(e.stage for e in engagements)
        artifact_counts = Counter(a.artifact_type for a in artifacts)
        active = [e for e in engagements if e.status not in {"closed", "lost"}]
        risks = [
            {"engagement_id": str(e.id), "name": e.name, **risk}
            for e in active
            for risk in (e.risks or [])
            if risk.get("status", "open") != "closed"
        ]
        next_actions = [
            {"engagement_id": str(e.id), "name": e.name, **action}
            for e in active
            for action in (e.next_actions or [])
            if action.get("status", "open") != "done"
        ]

        return PipelineSummary(
            stages=dict(stage_counts),
            active_engagements=len(active),
            open_risks=len(risks),
            next_actions=next_actions[:20],
            artifact_types=dict(artifact_counts),
        )

    async def export_agent_context(self) -> dict:
        from app.domains.case.models import SuccessCase
        from app.domains.customer.models import Customer
        from app.domains.graph.models import GraphEdge, GraphNode
        from app.domains.todo.models import Todo
        from app.domains.visit.models import VisitPlan, VisitRecord

        exports = {}
        for key, model in {
            "customers": Customer,
            "success_cases": SuccessCase,
            "engagements": Engagement,
            "artifacts": BusinessArtifact,
            "agent_action_logs": AgentActionLog,
            "graph_nodes": GraphNode,
            "graph_edges": GraphEdge,
            "visit_plans": VisitPlan,
            "visit_records": VisitRecord,
            "todos": Todo,
        }.items():
            rows = (await self.session.execute(select(model))).scalars().all()
            exports[key] = [_serialize_model(row) for row in rows]

        return {
            "format": "solocrm-agent-context-v2",
            "tables": exports,
        }


class AgentAuditService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def log(
        self,
        agent_name: str,
        action: str,
        target_type: str,
        target_id: UUID | None,
        request_json: dict,
        result_json: dict,
        status: str = "ok",
    ) -> AgentActionLog:
        instance = AgentActionLog(
            agent_name=agent_name,
            action=action,
            target_type=target_type,
            target_id=target_id,
            request_json=request_json,
            result_json=result_json,
            status=status,
        )
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance


def engagement_service(session: AsyncSession) -> EngagementService:
    return EngagementService(EngagementRepository(session))


def artifact_service(session: AsyncSession) -> ArtifactService:
    return ArtifactService(ArtifactRepository(session))


def _validate_stage(stage: str) -> None:
    allowed = {"sales", "presales", "contract", "delivery", "renewal", "closed"}
    if stage not in allowed:
        raise ValidationError(f"Unsupported engagement stage: {stage}", "stage")


def _serialize_model(instance) -> dict:
    result = {}
    for column in instance.__table__.columns:
        value = getattr(instance, column.name)
        if isinstance(value, UUID):
            value = str(value)
        elif isinstance(value, (datetime, date)):
            value = value.isoformat()
        elif isinstance(value, Decimal):
            value = float(value)
        elif value is not None:
            value = float(value) if str(column.type).startswith("NUMERIC") else value
        result[column.name] = value
    return result
