from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


ENGAGEMENT_STAGES = {"sales", "presales", "contract", "delivery", "renewal", "closed"}


class EngagementCreate(BaseModel):
    customer_id: UUID | None = None
    name: str = Field(..., max_length=200)
    company: str = Field(default="", max_length=200)
    stage: str = Field(default="sales", max_length=40)
    status: str = Field(default="active", max_length=40)
    owner: str = Field(default="", max_length=100)
    value: float | None = None
    close_date: datetime | None = None
    priority: int = Field(default=3, ge=1, le=5)
    sales_json: dict | None = None
    presales_json: dict | None = None
    delivery_json: dict | None = None
    next_actions: list[dict] | None = None
    risks: list[dict] | None = None
    tags: list[str] | None = None


class EngagementUpdate(BaseModel):
    customer_id: UUID | None = None
    name: str | None = Field(default=None, max_length=200)
    company: str | None = Field(default=None, max_length=200)
    stage: str | None = Field(default=None, max_length=40)
    status: str | None = Field(default=None, max_length=40)
    owner: str | None = Field(default=None, max_length=100)
    value: float | None = None
    close_date: datetime | None = None
    priority: int | None = Field(default=None, ge=1, le=5)
    sales_json: dict | None = None
    presales_json: dict | None = None
    delivery_json: dict | None = None
    next_actions: list[dict] | None = None
    risks: list[dict] | None = None
    tags: list[str] | None = None


class EngagementResponse(BaseModel):
    id: UUID
    customer_id: UUID | None
    name: str
    company: str
    stage: str
    status: str
    owner: str
    value: float | None
    close_date: datetime | None
    priority: int
    sales_json: dict | None
    presales_json: dict | None
    delivery_json: dict | None
    next_actions: list[dict] | None
    risks: list[dict] | None
    tags: list[str] | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ArtifactCreate(BaseModel):
    engagement_id: UUID | None = None
    customer_id: UUID | None = None
    artifact_type: str = Field(..., max_length=60)
    title: str = Field(..., max_length=240)
    content: str = ""
    summary: str = ""
    source: str = Field(default="manual", max_length=120)
    version: str = Field(default="1", max_length=40)
    metadata_json: dict | None = None
    tags: list[str] | None = None


class ArtifactUpdate(BaseModel):
    engagement_id: UUID | None = None
    customer_id: UUID | None = None
    artifact_type: str | None = Field(default=None, max_length=60)
    title: str | None = Field(default=None, max_length=240)
    content: str | None = None
    summary: str | None = None
    source: str | None = Field(default=None, max_length=120)
    version: str | None = Field(default=None, max_length=40)
    metadata_json: dict | None = None
    tags: list[str] | None = None


class ArtifactResponse(BaseModel):
    id: UUID
    engagement_id: UUID | None
    customer_id: UUID | None
    artifact_type: str
    title: str
    content: str
    summary: str
    source: str
    version: str
    metadata_json: dict | None
    tags: list[str] | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PipelineSummary(BaseModel):
    stages: dict[str, int]
    active_engagements: int
    open_risks: int
    next_actions: list[dict]
    artifact_types: dict[str, int]


class AgentActionLogResponse(BaseModel):
    id: UUID
    agent_name: str
    action: str
    target_type: str
    target_id: UUID | None
    request_json: dict | None
    result_json: dict | None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AgentAuditSummary(BaseModel):
    status_counts: dict[str, int]
    action_counts: dict[str, int]
    agent_counts: dict[str, int]
    latest_errors: list[AgentActionLogResponse]
