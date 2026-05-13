from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class CaseCreate(BaseModel):
    title: str = Field(..., max_length=200)
    company_name: str = Field(..., max_length=200)
    industry: str = Field(default="", max_length=100)
    city: str = Field(default="", max_length=100)
    product: str = Field(default="", max_length=200)
    deal_size: float | None = None
    summary: str = ""
    key_points: list[dict] | None = None


class CaseUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    company_name: str | None = Field(default=None, max_length=200)
    industry: str | None = Field(default=None, max_length=100)
    city: str | None = Field(default=None, max_length=100)
    product: str | None = Field(default=None, max_length=200)
    deal_size: float | None = None
    summary: str | None = None
    key_points: list[dict] | None = None


class CaseResponse(BaseModel):
    id: UUID
    title: str
    company_name: str
    industry: str
    city: str
    product: str
    deal_size: float | None
    summary: str
    key_points: list[dict] | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
