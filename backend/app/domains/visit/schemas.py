from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class VisitPlanCreate(BaseModel):
    customer_id: UUID
    planned_date: datetime
    location: str = Field(default="", max_length=300)
    latitude: float | None = None
    longitude: float | None = None
    purpose: str = ""
    notes: str = ""
    status: str = Field(default="planned", max_length=20)


class VisitPlanUpdate(BaseModel):
    planned_date: datetime | None = None
    location: str | None = Field(default=None, max_length=300)
    latitude: float | None = None
    longitude: float | None = None
    purpose: str | None = None
    notes: str | None = None
    status: str | None = Field(default=None, max_length=20)


class VisitPlanResponse(BaseModel):
    id: UUID
    customer_id: UUID
    planned_date: datetime
    location: str
    latitude: float | None
    longitude: float | None
    purpose: str
    notes: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class VisitRecordCreate(BaseModel):
    customer_id: UUID
    visit_date: datetime
    audio_path: str = ""
    transcript: str = ""
    summary: str = ""
    key_people: list[dict] | None = None
    meddic_update: dict | None = None
    action_items: list[dict] | None = None
    raw_notes: str = ""


class VisitRecordUpdate(BaseModel):
    visit_date: datetime | None = None
    audio_path: str | None = None
    transcript: str | None = None
    summary: str | None = None
    key_people: list[dict] | None = None
    meddic_update: dict | None = None
    action_items: list[dict] | None = None
    raw_notes: str | None = None


class VisitRecordResponse(BaseModel):
    id: UUID
    customer_id: UUID
    visit_date: datetime
    audio_path: str
    transcript: str
    summary: str
    key_people: list[dict] | None
    meddic_update: dict | None
    action_items: list[dict] | None
    raw_notes: str
    created_at: datetime

    model_config = {"from_attributes": True}
