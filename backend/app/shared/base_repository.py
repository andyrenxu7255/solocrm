from __future__ import annotations

from typing import Generic, Sequence, TypeVar
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.exceptions import NotFoundError
from app.shared.schemas import PaginationParams

ModelT = TypeVar("ModelT")


class BaseRepository(Generic[ModelT]):
    model: type[ModelT]

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, entity_id: UUID) -> ModelT:
        result = await self.session.execute(
            select(self.model).where(self.model.id == entity_id)
        )
        instance = result.scalar_one_or_none()
        if instance is None:
            raise NotFoundError(self.model.__name__, str(entity_id))
        return instance

    async def get_by_id_optional(self, entity_id: UUID) -> ModelT | None:
        result = await self.session.execute(
            select(self.model).where(self.model.id == entity_id)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        pagination: PaginationParams,
        order_by: str | None = "created_at",
        order_desc: bool = True,
    ) -> tuple[Sequence[ModelT], int]:
        count_q = select(func.count()).select_from(self.model)
        total = (await self.session.execute(count_q)).scalar_one()

        q = select(self.model)
        if order_by and hasattr(self.model, order_by):
            col = getattr(self.model, order_by)
            q = q.order_by(col.desc() if order_desc else col.asc())
        q = q.offset((pagination.page - 1) * pagination.page_size).limit(
            pagination.page_size
        )

        result = await self.session.execute(q)
        items = result.scalars().all()
        return items, total

    async def create(self, instance: ModelT) -> ModelT:
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def update(self, updated: ModelT) -> ModelT:
        await self.session.flush()
        await self.session.refresh(updated)
        return updated

    async def delete(self, instance: ModelT) -> None:
        await self.session.delete(instance)
        await self.session.flush()
