from __future__ import annotations

from app.domains.todo.models import Todo
from app.domains.todo.schemas import TodoCreate, TodoUpdate
from app.shared.base_service import BaseService


class TodoService(BaseService[Todo]):
    async def create_from_schema(self, data: TodoCreate) -> Todo:
        instance = Todo(**data.model_dump())
        return await self.repository.create(instance)

    async def update_from_schema(self, instance: Todo, data: TodoUpdate) -> Todo:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(instance, field, value)
        return await self.repository.update(instance)
