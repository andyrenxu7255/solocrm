from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.domains.graph.repository import GraphEdgeRepository, GraphNodeRepository
from app.domains.graph.schemas import (
    GraphEdgeCreate,
    GraphEdgeResponse,
    GraphFactInput,
    GraphFactResponse,
    GraphNodeCreate,
    GraphNodeResponse,
    GraphRecallRequest,
    GraphRecallResponse,
)
from app.domains.graph.service import (
    GraphEdgeService,
    GraphMemoryService,
    GraphNodeService,
)
from app.shared.schemas import APIResponse, PaginatedResponse, PaginationParams

router = APIRouter(prefix="/graph", tags=["Business Fact Graph"])


def _node_service(db: AsyncSession = Depends(get_db)) -> GraphNodeService:
    return GraphNodeService(GraphNodeRepository(db))


def _edge_service(db: AsyncSession = Depends(get_db)) -> GraphEdgeService:
    return GraphEdgeService(GraphEdgeRepository(db))


def _memory_service(db: AsyncSession = Depends(get_db)) -> GraphMemoryService:
    return GraphMemoryService(db)


@router.get("/nodes", response_model=APIResponse[PaginatedResponse[GraphNodeResponse]])
async def list_nodes(
    node_type: str | None = None,
    q: str | None = None,
    pagination: PaginationParams = Depends(),
    svc: GraphNodeService = Depends(_node_service),
):
    items, total = await svc.repository.list_filtered(pagination, node_type, q)
    return APIResponse.ok(
        PaginatedResponse.of(
            [GraphNodeResponse.model_validate(item) for item in items],
            total,
            pagination,
        )
    )


@router.get("/nodes/{node_id}", response_model=APIResponse[GraphNodeResponse])
async def get_node(
    node_id: UUID,
    svc: GraphNodeService = Depends(_node_service),
):
    item = await svc.repository.get_by_id(node_id)
    return APIResponse.ok(GraphNodeResponse.model_validate(item))


@router.post("/nodes", response_model=APIResponse[GraphNodeResponse], status_code=201)
async def create_node(
    body: GraphNodeCreate,
    svc: GraphNodeService = Depends(_node_service),
):
    item = await svc.create_from_schema(body)
    return APIResponse.ok(GraphNodeResponse.model_validate(item))


@router.get("/edges", response_model=APIResponse[PaginatedResponse[GraphEdgeResponse]])
async def list_edges(
    relation_type: str | None = None,
    node_id: UUID | None = None,
    pagination: PaginationParams = Depends(),
    svc: GraphEdgeService = Depends(_edge_service),
):
    items, total = await svc.repository.list_filtered(
        pagination,
        relation_type=relation_type,
        node_id=node_id,
    )
    return APIResponse.ok(
        PaginatedResponse.of(
            [GraphEdgeResponse.model_validate(item) for item in items],
            total,
            pagination,
        )
    )


@router.post("/edges", response_model=APIResponse[GraphEdgeResponse], status_code=201)
async def create_edge(
    body: GraphEdgeCreate,
    svc: GraphEdgeService = Depends(_edge_service),
):
    item = await svc.create_from_schema(body)
    return APIResponse.ok(GraphEdgeResponse.model_validate(item))


@router.post("/facts", response_model=APIResponse[GraphFactResponse], status_code=201)
async def upsert_fact(
    body: GraphFactInput,
    svc: GraphMemoryService = Depends(_memory_service),
):
    result = await svc.upsert_fact(body)
    return APIResponse.ok(result)


@router.post("/rebuild", response_model=APIResponse[GraphFactResponse])
async def rebuild_graph(
    svc: GraphMemoryService = Depends(_memory_service),
):
    result = await svc.rebuild_from_sources()
    return APIResponse.ok(result)


@router.post("/recall", response_model=APIResponse[GraphRecallResponse])
async def recall(
    body: GraphRecallRequest,
    svc: GraphMemoryService = Depends(_memory_service),
):
    result = await svc.recall(body)
    return APIResponse.ok(result)
