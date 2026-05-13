from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.domains.customer.repository import CustomerRepository
from app.domains.customer.schemas import CustomerCreate, CustomerResponse, CustomerUpdate
from app.domains.customer.service import CustomerService
from app.shared.schemas import APIResponse, PaginatedResponse, PaginationParams

router = APIRouter(prefix="/customers", tags=["Customers"])


def _service(db: AsyncSession = Depends(get_db)) -> CustomerService:
    return CustomerService(CustomerRepository(db))


@router.get("", response_model=APIResponse[PaginatedResponse[CustomerResponse]])
async def list_customers(
    pagination: PaginationParams = Depends(),
    svc: CustomerService = Depends(_service),
):
    items, total = await svc.repository.get_all(pagination)
    return APIResponse.ok(
        PaginatedResponse.of(
            [CustomerResponse.model_validate(i) for i in items], total, pagination
        )
    )


@router.get("/{customer_id}", response_model=APIResponse[CustomerResponse])
async def get_customer(
    customer_id: UUID,
    svc: CustomerService = Depends(_service),
):
    instance = await svc.repository.get_by_id(customer_id)
    return APIResponse.ok(CustomerResponse.model_validate(instance))


@router.post("", response_model=APIResponse[CustomerResponse], status_code=201)
async def create_customer(
    data: CustomerCreate,
    svc: CustomerService = Depends(_service),
):
    instance = await svc.create_from_schema(data)
    return APIResponse.ok(CustomerResponse.model_validate(instance))


@router.put("/{customer_id}", response_model=APIResponse[CustomerResponse])
async def update_customer(
    customer_id: UUID,
    data: CustomerUpdate,
    svc: CustomerService = Depends(_service),
):
    instance = await svc.repository.get_by_id(customer_id)
    updated = await svc.update_from_schema(instance, data)
    return APIResponse.ok(CustomerResponse.model_validate(updated))


@router.delete("/{customer_id}", response_model=APIResponse[None])
async def delete_customer(
    customer_id: UUID,
    svc: CustomerService = Depends(_service),
):
    instance = await svc.repository.get_by_id(customer_id)
    await svc.repository.delete(instance)
    return APIResponse.ok(None, "deleted")
