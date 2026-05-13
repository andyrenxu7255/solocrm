from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.domains.case.repository import CaseRepository
from app.domains.case.schemas import CaseCreate, CaseResponse, CaseUpdate
from app.domains.case.service import CaseService
from app.shared.schemas import APIResponse, PaginatedResponse, PaginationParams

router = APIRouter(prefix="/cases", tags=["Cases"])


def _service(db: AsyncSession = Depends(get_db)) -> CaseService:
    return CaseService(CaseRepository(db))


@router.get("", response_model=APIResponse[PaginatedResponse[CaseResponse]])
async def list_cases(
    pagination: PaginationParams = Depends(),
    svc: CaseService = Depends(_service),
):
    items, total = await svc.repository.get_all(pagination)
    return APIResponse.ok(
        PaginatedResponse.of(
            [CaseResponse.model_validate(i) for i in items], total, pagination
        )
    )


@router.get("/{case_id}", response_model=APIResponse[CaseResponse])
async def get_case(
    case_id: UUID,
    svc: CaseService = Depends(_service),
):
    instance = await svc.repository.get_by_id(case_id)
    return APIResponse.ok(CaseResponse.model_validate(instance))


@router.post("", response_model=APIResponse[CaseResponse], status_code=201)
async def create_case(
    data: CaseCreate,
    svc: CaseService = Depends(_service),
):
    instance = await svc.create_from_schema(data)
    return APIResponse.ok(CaseResponse.model_validate(instance))


@router.put("/{case_id}", response_model=APIResponse[CaseResponse])
async def update_case(
    case_id: UUID,
    data: CaseUpdate,
    svc: CaseService = Depends(_service),
):
    instance = await svc.repository.get_by_id(case_id)
    updated = await svc.update_from_schema(instance, data)
    return APIResponse.ok(CaseResponse.model_validate(updated))


@router.delete("/{case_id}", response_model=APIResponse[None])
async def delete_case(
    case_id: UUID,
    svc: CaseService = Depends(_service),
):
    instance = await svc.repository.get_by_id(case_id)
    await svc.repository.delete(instance)
    return APIResponse.ok(None, "deleted")


class CaseExtractRequest(BaseModel):
    content: str = Field(..., min_length=10, max_length=5000, description="Natural language description of the case")


@router.post("/extract", response_model=APIResponse[CaseResponse], status_code=201)
async def extract_case(
    body: CaseExtractRequest,
    svc: CaseService = Depends(_service),
):
    instance = await svc.extract_from_conversation(body.content)
    return APIResponse.ok(CaseResponse.model_validate(instance))
