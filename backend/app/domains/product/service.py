from __future__ import annotations

from app.domains.product.models import UserProductConfig
from app.domains.product.schemas import ProductConfigCreate, ProductConfigUpdate
from app.shared.base_service import BaseService


class ProductConfigService(BaseService[UserProductConfig]):
    async def create_from_schema(self, data: ProductConfigCreate) -> UserProductConfig:
        instance = UserProductConfig(**data.model_dump())
        return await self.repository.create(instance)

    async def update_from_schema(
        self, instance: UserProductConfig, data: ProductConfigUpdate
    ) -> UserProductConfig:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(instance, field, value)
        return await self.repository.update(instance)
