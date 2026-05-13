from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int

    @classmethod
    def of(
        cls,
        items: list[T],
        total: int,
        params: PaginationParams,
    ) -> PaginatedResponse[T]:
        return cls(
            items=items,
            total=total,
            page=params.page,
            page_size=params.page_size,
            total_pages=(total + params.page_size - 1) // params.page_size,
        )


class APIResponse(BaseModel, Generic[T]):
    code: int = 0
    data: T | None = None
    message: str = "success"

    @classmethod
    def ok(cls, data: T, message: str = "success") -> APIResponse[T]:
        return cls(code=0, data=data, message=message)

    @classmethod
    def error(cls, message: str, code: int = 1) -> APIResponse[None]:
        return cls(code=code, data=None, message=message)
