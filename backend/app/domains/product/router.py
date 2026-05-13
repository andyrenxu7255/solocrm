from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.domains.product.repository import ProductConfigRepository
from app.domains.product.schemas import (
    ProductConfigCreate,
    ProductConfigResponse,
    ProductConfigUpdate,
)
from app.domains.product.service import ProductConfigService
from app.shared.schemas import APIResponse, PaginatedResponse, PaginationParams

router = APIRouter(prefix="/products", tags=["Product Config"])


def _service(db: AsyncSession = Depends(get_db)) -> ProductConfigService:
    return ProductConfigService(ProductConfigRepository(db))


@router.get("", response_model=APIResponse[PaginatedResponse[ProductConfigResponse]])
async def list_products(
    pagination: PaginationParams = Depends(),
    svc: ProductConfigService = Depends(_service),
):
    items, total = await svc.repository.get_all(pagination)
    return APIResponse.ok(
        PaginatedResponse.of(
            [ProductConfigResponse.model_validate(i) for i in items], total, pagination
        )
    )


@router.get("/{product_id}", response_model=APIResponse[ProductConfigResponse])
async def get_product(product_id: UUID, svc: ProductConfigService = Depends(_service)):
    instance = await svc.repository.get_by_id(product_id)
    return APIResponse.ok(ProductConfigResponse.model_validate(instance))


@router.post("", response_model=APIResponse[ProductConfigResponse], status_code=201)
async def create_product(
    data: ProductConfigCreate, svc: ProductConfigService = Depends(_service)
):
    instance = await svc.create_from_schema(data)
    return APIResponse.ok(ProductConfigResponse.model_validate(instance))


@router.put("/{product_id}", response_model=APIResponse[ProductConfigResponse])
async def update_product(
    product_id: UUID,
    data: ProductConfigUpdate,
    svc: ProductConfigService = Depends(_service),
):
    instance = await svc.repository.get_by_id(product_id)
    updated = await svc.update_from_schema(instance, data)
    return APIResponse.ok(ProductConfigResponse.model_validate(updated))


@router.delete("/{product_id}", response_model=APIResponse[None])
async def delete_product(
    product_id: UUID, svc: ProductConfigService = Depends(_service)
):
    instance = await svc.repository.get_by_id(product_id)
    await svc.repository.delete(instance)
    return APIResponse.ok(None, "deleted")
