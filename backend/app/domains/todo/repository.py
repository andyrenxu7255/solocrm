from __future__ import annotations

from app.domains.todo.models import Todo
from app.shared.base_repository import BaseRepository


class TodoRepository(BaseRepository[Todo]):
    model = Todo
