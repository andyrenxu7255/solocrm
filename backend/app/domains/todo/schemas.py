from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class TodoCreate(BaseModel):
    customer_id: UUID | None = None
    title: str = Field(..., max_length=300)
    description: str = ""
    priority: int = Field(default=0, ge=0)
    meddic_dim: str = Field(default="", max_length=30)
    due_date: date | None = None
    status: str = Field(default="pending", max_length=20)
    source: str = Field(default="manual", max_length=30)


class TodoUpdate(BaseModel):
    customer_id: UUID | None = None
    title: str | None = Field(default=None, max_length=300)
    description: str | None = None
    priority: int | None = Field(default=None, ge=0)
    meddic_dim: str | None = Field(default=None, max_length=30)
    due_date: date | None = None
    status: str | None = Field(default=None, max_length=20)
    source: str | None = Field(default=None, max_length=30)


class TodoResponse(BaseModel):
    id: UUID
    customer_id: UUID | None
    title: str
    description: str
    priority: int
    meddic_dim: str
    due_date: date | None
    status: str
    source: str
    created_at: datetime

    model_config = {"from_attributes": True}
