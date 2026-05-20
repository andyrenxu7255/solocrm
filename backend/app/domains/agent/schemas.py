from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class AgentActionRequest(BaseModel):
    agent_name: str = Field(default="unknown", max_length=100)
    action: str = Field(..., max_length=80)
    payload: dict[str, Any] = Field(default_factory=dict)


class AgentActionResponse(BaseModel):
    action: str
    target_type: str
    target_id: str | None = None
    result: dict[str, Any]
    audit_id: str

