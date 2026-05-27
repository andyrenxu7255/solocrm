from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


GRAPH_NODE_TYPES = {
    "industry",
    "customer",
    "domain",
    "project",
    "case",
    "artifact",
    "product",
    "city",
}

GRAPH_RELATION_TYPES = {
    "in_industry",
    "serves_domain",
    "has_project",
    "uses_product",
    "located_in",
    "has_case",
    "supports_artifact",
    "similar_to",
    "references",
}


class GraphNodeCreate(BaseModel):
    node_type: str = Field(..., max_length=50)
    name: str = Field(..., max_length=240)
    description: str = ""
    source_type: str = Field(default="manual", max_length=80)
    source_id: UUID | None = None
    properties_json: dict | None = None


class GraphNodeResponse(BaseModel):
    id: UUID
    node_type: str
    name: str
    canonical_name: str
    description: str
    source_type: str
    source_id: UUID | None
    properties_json: dict | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class GraphEdgeCreate(BaseModel):
    from_node_id: UUID
    relation_type: str = Field(..., max_length=80)
    to_node_id: UUID
    weight: float = Field(default=1.0, ge=0.0, le=10.0)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    source_type: str = Field(default="manual", max_length=80)
    source_id: UUID | None = None
    evidence: str = ""
    properties_json: dict | None = None


class GraphEdgeResponse(BaseModel):
    id: UUID
    from_node_id: UUID
    relation_type: str
    to_node_id: UUID
    weight: float
    confidence: float
    source_type: str
    source_id: UUID | None
    evidence: str
    properties_json: dict | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class GraphFactInput(BaseModel):
    industry: str | None = Field(default=None, max_length=100)
    customer: str | None = Field(default=None, max_length=200)
    domain: str | None = Field(default=None, max_length=200)
    project: str | None = Field(default=None, max_length=240)
    case_id: UUID | None = None
    engagement_id: UUID | None = None
    artifact_id: UUID | None = None
    product: str | None = Field(default=None, max_length=200)
    city: str | None = Field(default=None, max_length=100)
    evidence: str = ""
    source_type: str = Field(default="agent", max_length=80)
    source_id: UUID | None = None
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class GraphFactResponse(BaseModel):
    nodes: list[GraphNodeResponse]
    edges: list[GraphEdgeResponse]


class GraphRecallRequest(BaseModel):
    industry: str | None = Field(default=None, max_length=100)
    customer: str | None = Field(default=None, max_length=200)
    domain: str | None = Field(default=None, max_length=200)
    project: str | None = Field(default=None, max_length=240)
    query: str | None = Field(default=None, max_length=1000)
    include_artifacts: bool = True
    limit: int = Field(default=10, ge=1, le=50)


class GraphPathStep(BaseModel):
    from_node: GraphNodeResponse
    relation_type: str
    to_node: GraphNodeResponse
    evidence: str
    confidence: float


class GraphRecallItem(BaseModel):
    target_type: str
    target_id: UUID | None
    title: str
    score: float
    shared_nodes: list[GraphNodeResponse]
    paths: list[GraphPathStep]
    payload: dict


class GraphRecallResponse(BaseModel):
    query_nodes: list[GraphNodeResponse]
    items: list[GraphRecallItem]
    gate: dict
