from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.domains.todo.repository import TodoRepository
from app.domains.todo.schemas import TodoCreate, TodoResponse, TodoUpdate
from app.domains.todo.service import TodoService
from app.shared.schemas import APIResponse, PaginatedResponse, PaginationParams

router = APIRouter(prefix="/todos", tags=["Todos"])


def _service(db: AsyncSession = Depends(get_db)) -> TodoService:
    return TodoService(TodoRepository(db))


@router.get("", response_model=APIResponse[PaginatedResponse[TodoResponse]])
async def list_todos(
    pagination: PaginationParams = Depends(),
    svc: TodoService = Depends(_service),
):
    items, total = await svc.repository.get_all(pagination, order_by="priority")
    return APIResponse.ok(
        PaginatedResponse.of(
            [TodoResponse.model_validate(i) for i in items], total, pagination
        )
    )


@router.get("/{todo_id}", response_model=APIResponse[TodoResponse])
async def get_todo(todo_id: UUID, svc: TodoService = Depends(_service)):
    instance = await svc.repository.get_by_id(todo_id)
    return APIResponse.ok(TodoResponse.model_validate(instance))


@router.post("", response_model=APIResponse[TodoResponse], status_code=201)
async def create_todo(data: TodoCreate, svc: TodoService = Depends(_service)):
    instance = await svc.create_from_schema(data)
    return APIResponse.ok(TodoResponse.model_validate(instance))


@router.put("/{todo_id}", response_model=APIResponse[TodoResponse])
async def update_todo(
    todo_id: UUID, data: TodoUpdate, svc: TodoService = Depends(_service)
):
    instance = await svc.repository.get_by_id(todo_id)
    updated = await svc.update_from_schema(instance, data)
    return APIResponse.ok(TodoResponse.model_validate(updated))


@router.delete("/{todo_id}", response_model=APIResponse[None])
async def delete_todo(todo_id: UUID, svc: TodoService = Depends(_service)):
    instance = await svc.repository.get_by_id(todo_id)
    await svc.repository.delete(instance)
    return APIResponse.ok(None, "deleted")
