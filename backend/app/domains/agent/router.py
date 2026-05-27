from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.domains.agent.schemas import AgentActionRequest, AgentActionResponse
from app.domains.business.schemas import (
    ArtifactCreate,
    ArtifactResponse,
    EngagementCreate,
    EngagementResponse,
    EngagementUpdate,
)
from app.domains.business.service import (
    AgentAuditService,
    BusinessReadService,
    artifact_service,
    engagement_service,
)
from app.domains.graph.schemas import GraphFactInput, GraphRecallRequest
from app.domains.graph.service import GraphMemoryService
from app.shared.exceptions import NotFoundError, ValidationError
from app.shared.schemas import APIResponse

router = APIRouter(prefix="/agent", tags=["Agent Protocol"])

ACTION_DESCRIPTIONS = {
    "create_engagement": "Create a sales/presales/delivery business process.",
    "update_engagement": "Patch an engagement by id.",
    "advance_stage": "Move an engagement to sales, presales, contract, delivery, renewal, or closed.",
    "add_artifact": "Persist contract templates, knowledge, proposals, delivery notes, or other portable assets.",
    "get_pipeline_summary": "Return structured sales/presales/delivery summary for planning.",
    "upsert_graph_fact": "Create or update business graph facts for industry/customer/domain/project relationships.",
    "graph_recall": "Recall cases and artifacts through graph-gated relationships before semantic ranking.",
    "rebuild_graph": "Rebuild graph memory from customers, cases, engagements, and artifacts.",
}


@router.get("/capabilities", response_model=APIResponse[dict])
async def capabilities():
    return APIResponse.ok(
        {
            "version": "2026-05-20",
            "actions": ACTION_DESCRIPTIONS,
            "engagement_stages": [
                "sales",
                "presales",
                "contract",
                "delivery",
                "renewal",
                "closed",
            ],
            "artifact_types": [
                "contract_template",
                "knowledge",
                "proposal",
                "delivery_note",
                "meeting_note",
                "playbook",
            ],
            "graph_node_types": [
                "industry",
                "customer",
                "domain",
                "project",
                "case",
                "artifact",
                "product",
                "city",
            ],
        }
    )


@router.post("/actions", response_model=APIResponse[AgentActionResponse])
async def run_action(
    body: AgentActionRequest,
    db: AsyncSession = Depends(get_db),
):
    action = body.action.strip()
    payload = body.payload
    target_type = ""
    target_id: UUID | None = None
    result: dict = {}

    try:
        if action == "create_engagement":
            engagement = await engagement_service(db).create_from_schema(
                EngagementCreate.model_validate(payload)
            )
            target_type = "engagement"
            target_id = engagement.id
            result = EngagementResponse.model_validate(engagement).model_dump(
                mode="json"
            )

        elif action == "update_engagement":
            engagement_id = _require_uuid(payload, "engagement_id")
            target_type = "engagement"
            target_id = engagement_id
            patch = {k: v for k, v in payload.items() if k != "engagement_id"}
            svc = engagement_service(db)
            engagement = await svc.repository.get_by_id(engagement_id)
            updated = await svc.update_from_schema(
                engagement, EngagementUpdate.model_validate(patch)
            )
            target_id = updated.id
            result = EngagementResponse.model_validate(updated).model_dump(
                mode="json"
            )

        elif action == "advance_stage":
            engagement_id = _require_uuid(payload, "engagement_id")
            target_type = "engagement"
            target_id = engagement_id
            next_stage = payload.get("stage")
            if not next_stage:
                raise ValidationError("stage is required", "stage")
            svc = engagement_service(db)
            engagement = await svc.repository.get_by_id(engagement_id)
            patch = EngagementUpdate(
                stage=next_stage,
                status=payload.get("status"),
                next_actions=payload.get("next_actions"),
                risks=payload.get("risks"),
            )
            updated = await svc.update_from_schema(engagement, patch)
            target_id = updated.id
            result = EngagementResponse.model_validate(updated).model_dump(
                mode="json"
            )

        elif action == "add_artifact":
            artifact = await artifact_service(db).create_from_schema(
                ArtifactCreate.model_validate(payload)
            )
            target_type = "artifact"
            target_id = artifact.id
            result = ArtifactResponse.model_validate(artifact).model_dump(mode="json")

        elif action == "get_pipeline_summary":
            summary = await BusinessReadService(db).summarize_pipeline()
            target_type = "business_summary"
            result = summary.model_dump(mode="json")

        elif action == "upsert_graph_fact":
            graph = await GraphMemoryService(db).upsert_fact(
                GraphFactInput.model_validate(payload)
            )
            target_type = "graph_fact"
            result = graph.model_dump(mode="json")

        elif action == "graph_recall":
            recall = await GraphMemoryService(db).recall(
                GraphRecallRequest.model_validate(payload)
            )
            target_type = "graph_recall"
            result = recall.model_dump(mode="json")

        elif action == "rebuild_graph":
            graph = await GraphMemoryService(db).rebuild_from_sources()
            target_type = "graph_rebuild"
            result = {
                "nodes": len(graph.nodes),
                "edges": len(graph.edges),
            }

        else:
            raise ValidationError(f"Unsupported agent action: {action}", "action")
    except PydanticValidationError as exc:
        await AgentAuditService(db).log(
            agent_name=body.agent_name,
            action=action,
            target_type=target_type,
            target_id=target_id,
            request_json=body.model_dump(mode="json"),
            result_json={"error": str(exc), "error_type": "payload_validation"},
            status="error",
        )
        return APIResponse.error(str(exc), code=1)
    except (ValidationError, NotFoundError) as exc:
        await AgentAuditService(db).log(
            agent_name=body.agent_name,
            action=action,
            target_type=target_type,
            target_id=target_id,
            request_json=body.model_dump(mode="json"),
            result_json={"error": str(exc), "error_type": exc.__class__.__name__},
            status="error",
        )
        return APIResponse.error(str(exc), code=1)

    audit = await AgentAuditService(db).log(
        agent_name=body.agent_name,
        action=action,
        target_type=target_type,
        target_id=target_id,
        request_json=body.model_dump(mode="json"),
        result_json=result,
        status="ok",
    )

    return APIResponse.ok(
        AgentActionResponse(
            action=action,
            target_type=target_type,
            target_id=str(target_id) if target_id else None,
            result=result,
            audit_id=str(audit.id),
        )
    )


def _require_uuid(payload: dict, key: str) -> UUID:
    raw = payload.get(key)
    if not raw:
        raise ValidationError(f"{key} is required", key)
    try:
        return UUID(str(raw))
    except ValueError as exc:
        raise ValidationError(f"{key} must be a UUID", key) from exc
