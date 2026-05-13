from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class CustomerCreate(BaseModel):
    name: str = Field(..., max_length=100)
    company: str = Field(default="", max_length=200)
    title: str = Field(default="", max_length=100)
    industry: str = Field(default="", max_length=100)
    city: str = Field(default="", max_length=100)
    contact_info: dict | None = None
    source: str = Field(default="manual", max_length=50)
    status: str = Field(default="new", max_length=30)
    notes: str = ""
    tags: list[str] | None = None
    meddic_json: dict | None = None


class CustomerUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=100)
    company: str | None = Field(default=None, max_length=200)
    title: str | None = Field(default=None, max_length=100)
    industry: str | None = Field(default=None, max_length=100)
    city: str | None = Field(default=None, max_length=100)
    contact_info: dict | None = None
    source: str | None = Field(default=None, max_length=50)
    status: str | None = Field(default=None, max_length=30)
    notes: str | None = None
    tags: list[str] | None = None
    meddic_json: dict | None = None


class CustomerResponse(BaseModel):
    id: UUID
    name: str
    company: str
    title: str
    industry: str
    city: str
    contact_info: dict | None
    source: str
    status: str
    notes: str
    tags: list[str] | None
    meddic_json: dict | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
