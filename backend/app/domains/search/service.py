from __future__ import annotations

from typing import Any, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.case.models import SuccessCase
from app.domains.customer.models import Customer


class SearchService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def search_customers(
        self,
        industry: str | None = None,
        city: str | None = None,
        limit: int = 20,
    ) -> Sequence[Customer]:
        q = select(Customer)
        if industry:
            q = q.where(Customer.industry == industry)
        if city:
            q = q.where(Customer.city == city)
        q = q.limit(limit)
        result = await self.session.execute(q)
        return result.scalars().all()

    async def search_cases(
        self,
        industry: str | None = None,
        city: str | None = None,
        limit: int = 20,
    ) -> Sequence[SuccessCase]:
        q = select(SuccessCase)
        if industry:
            q = q.where(SuccessCase.industry == industry)
        if city:
            q = q.where(SuccessCase.city == city)
        q = q.limit(limit)
        result = await self.session.execute(q)
        return result.scalars().all()
