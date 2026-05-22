from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.domains.business.repository import ArtifactRepository, EngagementRepository
from app.domains.business.repository import AgentActionLogRepository
from app.domains.business.schemas import (
    AgentActionLogResponse,
    AgentAuditSummary,
    ArtifactCreate,
    ArtifactResponse,
    ArtifactUpdate,
    EngagementCreate,
    EngagementResponse,
    EngagementUpdate,
    PipelineSummary,
)
from app.domains.business.service import (
    ArtifactService,
    BusinessReadService,
    EngagementService,
)
from app.shared.schemas import APIResponse, PaginatedResponse, PaginationParams

engagement_router = APIRouter(prefix="/engagements", tags=["Business Engagements"])
artifact_router = APIRouter(prefix="/artifacts", tags=["Business Artifacts"])
business_router = APIRouter(prefix="/business", tags=["Business Summary"])
audit_router = APIRouter(prefix="/agent/audit", tags=["Agent Audit"])


def _engagement_service(db: AsyncSession = Depends(get_db)) -> EngagementService:
    return EngagementService(EngagementRepository(db))


def _artifact_service(db: AsyncSession = Depends(get_db)) -> ArtifactService:
    return ArtifactService(ArtifactRepository(db))


def _audit_repository(
    db: AsyncSession = Depends(get_db),
) -> AgentActionLogRepository:
    return AgentActionLogRepository(db)


@engagement_router.get(
    "", response_model=APIResponse[PaginatedResponse[EngagementResponse]]
)
async def list_engagements(
    stage: str | None = None,
    status: str | None = None,
    pagination: PaginationParams = Depends(),
    svc: EngagementService = Depends(_engagement_service),
):
    items, total = await svc.repository.get_filtered(pagination, stage, status)
    return APIResponse.ok(
        PaginatedResponse.of(
            [EngagementResponse.model_validate(i) for i in items], total, pagination
        )
    )


@engagement_router.get("/{engagement_id}", response_model=APIResponse[EngagementResponse])
async def get_engagement(
    engagement_id: UUID,
    svc: EngagementService = Depends(_engagement_service),
):
    instance = await svc.repository.get_by_id(engagement_id)
    return APIResponse.ok(EngagementResponse.model_validate(instance))


@engagement_router.post(
    "", response_model=APIResponse[EngagementResponse], status_code=201
)
async def create_engagement(
    data: EngagementCreate,
    svc: EngagementService = Depends(_engagement_service),
):
    instance = await svc.create_from_schema(data)
    return APIResponse.ok(EngagementResponse.model_validate(instance))


@engagement_router.put("/{engagement_id}", response_model=APIResponse[EngagementResponse])
async def update_engagement(
    engagement_id: UUID,
    data: EngagementUpdate,
    svc: EngagementService = Depends(_engagement_service),
):
    instance = await svc.repository.get_by_id(engagement_id)
    updated = await svc.update_from_schema(instance, data)
    return APIResponse.ok(EngagementResponse.model_validate(updated))


@engagement_router.delete("/{engagement_id}", response_model=APIResponse[None])
async def delete_engagement(
    engagement_id: UUID,
    svc: EngagementService = Depends(_engagement_service),
):
    instance = await svc.repository.get_by_id(engagement_id)
    await svc.repository.delete(instance)
    return APIResponse.ok(None, "deleted")


@artifact_router.get("", response_model=APIResponse[PaginatedResponse[ArtifactResponse]])
async def list_artifacts(
    pagination: PaginationParams = Depends(),
    svc: ArtifactService = Depends(_artifact_service),
):
    items, total = await svc.repository.get_all(pagination)
    return APIResponse.ok(
        PaginatedResponse.of(
            [ArtifactResponse.model_validate(i) for i in items], total, pagination
        )
    )


@artifact_router.get("/{artifact_id}", response_model=APIResponse[ArtifactResponse])
async def get_artifact(
    artifact_id: UUID,
    svc: ArtifactService = Depends(_artifact_service),
):
    instance = await svc.repository.get_by_id(artifact_id)
    return APIResponse.ok(ArtifactResponse.model_validate(instance))


@artifact_router.post("", response_model=APIResponse[ArtifactResponse], status_code=201)
async def create_artifact(
    data: ArtifactCreate,
    svc: ArtifactService = Depends(_artifact_service),
):
    instance = await svc.create_from_schema(data)
    return APIResponse.ok(ArtifactResponse.model_validate(instance))


@artifact_router.put("/{artifact_id}", response_model=APIResponse[ArtifactResponse])
async def update_artifact(
    artifact_id: UUID,
    data: ArtifactUpdate,
    svc: ArtifactService = Depends(_artifact_service),
):
    instance = await svc.repository.get_by_id(artifact_id)
    updated = await svc.update_from_schema(instance, data)
    return APIResponse.ok(ArtifactResponse.model_validate(updated))


@artifact_router.delete("/{artifact_id}", response_model=APIResponse[None])
async def delete_artifact(
    artifact_id: UUID,
    svc: ArtifactService = Depends(_artifact_service),
):
    instance = await svc.repository.get_by_id(artifact_id)
    await svc.repository.delete(instance)
    return APIResponse.ok(None, "deleted")


@business_router.get("/summary", response_model=APIResponse[PipelineSummary])
async def business_summary(db: AsyncSession = Depends(get_db)):
    summary = await BusinessReadService(db).summarize_pipeline()
    return APIResponse.ok(summary)


@business_router.get("/export", response_model=APIResponse[dict])
async def business_export(db: AsyncSession = Depends(get_db)):
    export = await BusinessReadService(db).export_agent_context()
    return APIResponse.ok(export)


@audit_router.get(
    "", response_model=APIResponse[PaginatedResponse[AgentActionLogResponse]]
)
async def list_agent_audit_logs(
    agent_name: str | None = None,
    action: str | None = None,
    status: str | None = None,
    target_type: str | None = None,
    pagination: PaginationParams = Depends(),
    repo: AgentActionLogRepository = Depends(_audit_repository),
):
    items, total = await repo.get_filtered(
        pagination,
        agent_name=agent_name,
        action=action,
        status=status,
        target_type=target_type,
    )
    return APIResponse.ok(
        PaginatedResponse.of(
            [AgentActionLogResponse.model_validate(i) for i in items],
            total,
            pagination,
        )
    )


@audit_router.get("/summary", response_model=APIResponse[AgentAuditSummary])
async def summarize_agent_audit_logs(
    repo: AgentActionLogRepository = Depends(_audit_repository),
):
    summary = await repo.get_summary()
    return APIResponse.ok(
        AgentAuditSummary(
            status_counts=summary["status_counts"],
            action_counts=summary["action_counts"],
            agent_counts=summary["agent_counts"],
            latest_errors=[
                AgentActionLogResponse.model_validate(item)
                for item in summary["latest_errors"]
            ],
        )
    )


@audit_router.get("/{audit_id}", response_model=APIResponse[AgentActionLogResponse])
async def get_agent_audit_log(
    audit_id: UUID,
    repo: AgentActionLogRepository = Depends(_audit_repository),
):
    item = await repo.get_by_id(audit_id)
    return APIResponse.ok(AgentActionLogResponse.model_validate(item))
