from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.domains.visit.repository import VisitPlanRepository, VisitRecordRepository
from app.domains.visit.schemas import (
    VisitPlanCreate,
    VisitPlanResponse,
    VisitPlanUpdate,
    VisitRecordCreate,
    VisitRecordResponse,
    VisitRecordUpdate,
)
from app.domains.visit.service import VisitPlanService, VisitRecordService
from app.shared.schemas import APIResponse, PaginatedResponse, PaginationParams

plan_router = APIRouter(prefix="/visits/plans", tags=["Visit Plans"])
record_router = APIRouter(prefix="/visits/records", tags=["Visit Records"])


def _plan_service(db: AsyncSession = Depends(get_db)) -> VisitPlanService:
    return VisitPlanService(VisitPlanRepository(db))


def _record_service(db: AsyncSession = Depends(get_db)) -> VisitRecordService:
    return VisitRecordService(VisitRecordRepository(db))


# -- Visit Plans --

@plan_router.get("", response_model=APIResponse[PaginatedResponse[VisitPlanResponse]])
async def list_plans(
    pagination: PaginationParams = Depends(),
    svc: VisitPlanService = Depends(_plan_service),
):
    items, total = await svc.repository.get_all(pagination, order_by="planned_date", order_desc=False)
    return APIResponse.ok(
        PaginatedResponse.of(
            [VisitPlanResponse.model_validate(i) for i in items], total, pagination
        )
    )


@plan_router.get("/{plan_id}", response_model=APIResponse[VisitPlanResponse])
async def get_plan(plan_id: UUID, svc: VisitPlanService = Depends(_plan_service)):
    instance = await svc.repository.get_by_id(plan_id)
    return APIResponse.ok(VisitPlanResponse.model_validate(instance))


@plan_router.post("", response_model=APIResponse[VisitPlanResponse], status_code=201)
async def create_plan(data: VisitPlanCreate, svc: VisitPlanService = Depends(_plan_service)):
    instance = await svc.create_from_schema(data)
    return APIResponse.ok(VisitPlanResponse.model_validate(instance))


@plan_router.put("/{plan_id}", response_model=APIResponse[VisitPlanResponse])
async def update_plan(
    plan_id: UUID, data: VisitPlanUpdate, svc: VisitPlanService = Depends(_plan_service)
):
    instance = await svc.repository.get_by_id(plan_id)
    updated = await svc.update_from_schema(instance, data)
    return APIResponse.ok(VisitPlanResponse.model_validate(updated))


@plan_router.delete("/{plan_id}", response_model=APIResponse[None])
async def delete_plan(plan_id: UUID, svc: VisitPlanService = Depends(_plan_service)):
    instance = await svc.repository.get_by_id(plan_id)
    await svc.repository.delete(instance)
    return APIResponse.ok(None, "deleted")


# -- Visit Records --

@record_router.get("", response_model=APIResponse[PaginatedResponse[VisitRecordResponse]])
async def list_records(
    pagination: PaginationParams = Depends(),
    svc: VisitRecordService = Depends(_record_service),
):
    items, total = await svc.repository.get_all(pagination, order_by="visit_date")
    return APIResponse.ok(
        PaginatedResponse.of(
            [VisitRecordResponse.model_validate(i) for i in items], total, pagination
        )
    )


@record_router.get("/{record_id}", response_model=APIResponse[VisitRecordResponse])
async def get_record(record_id: UUID, svc: VisitRecordService = Depends(_record_service)):
    instance = await svc.repository.get_by_id(record_id)
    return APIResponse.ok(VisitRecordResponse.model_validate(instance))


@record_router.post("", response_model=APIResponse[VisitRecordResponse], status_code=201)
async def create_record(
    customer_id: UUID = Form(...),
    visit_date: str = Form(...),
    raw_notes: str = Form(default=""),
    audio: UploadFile | None = File(default=None),
    svc: VisitRecordService = Depends(_record_service),
):
    from datetime import datetime
    data = VisitRecordCreate(
        customer_id=customer_id,
        visit_date=datetime.fromisoformat(visit_date),
        raw_notes=raw_notes,
    )
    instance = await svc.create_with_audio(data, audio)
    if instance.transcript:
        instance = await svc.generate_ai_summary(instance)
    return APIResponse.ok(VisitRecordResponse.model_validate(instance))


@record_router.put("/{record_id}", response_model=APIResponse[VisitRecordResponse])
async def update_record(
    record_id: UUID, data: VisitRecordUpdate, svc: VisitRecordService = Depends(_record_service)
):
    instance = await svc.repository.get_by_id(record_id)
    updated = await svc.update_from_schema(instance, data)
    return APIResponse.ok(VisitRecordResponse.model_validate(updated))


@record_router.post("/{record_id}/summarize", response_model=APIResponse[VisitRecordResponse])
async def summarize_record(
    record_id: UUID,
    svc: VisitRecordService = Depends(_record_service),
):
    instance = await svc.repository.get_by_id(record_id)
    updated = await svc.generate_ai_summary(instance)
    return APIResponse.ok(VisitRecordResponse.model_validate(updated))
