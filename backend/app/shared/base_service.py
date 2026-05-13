from __future__ import annotations

from typing import Generic, TypeVar

from app.shared.base_repository import BaseRepository, ModelT


class BaseService(Generic[ModelT]):
    repository: BaseRepository[ModelT]

    def __init__(self, repository: BaseRepository[ModelT]) -> None:
        self.repository = repository
