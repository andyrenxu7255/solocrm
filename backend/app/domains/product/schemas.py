from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ProductConfigCreate(BaseModel):
    product_name: str = Field(..., max_length=200)
    description: str = ""
    features: list[dict] | None = None
    target_industries: list[str] | None = None


class ProductConfigUpdate(BaseModel):
    product_name: str | None = Field(default=None, max_length=200)
    description: str | None = None
    features: list[dict] | None = None
    target_industries: list[str] | None = None


class ProductConfigResponse(BaseModel):
    id: UUID
    product_name: str
    description: str
    features: list[dict] | None
    target_industries: list[str] | None
    created_at: datetime

    model_config = {"from_attributes": True}
