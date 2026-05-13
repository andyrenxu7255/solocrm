from __future__ import annotations

from typing import Sequence

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.case.models import SuccessCase
from app.domains.customer.models import Customer
from app.domains.search.service import SearchService


class HybridSearchService(SearchService):
    async def search_customers_hybrid(
        self,
        query_embedding: list[float] | None = None,
        industry: str | None = None,
        city: str | None = None,
        limit: int = 20,
    ) -> Sequence[Customer]:
        base = "SELECT c.* FROM customers c"
        conditions = []
        params: dict = {"limit": limit}

        if industry:
            conditions.append("c.industry = :industry")
            params["industry"] = industry
        if city:
            conditions.append("c.city = :city")
            params["city"] = city

        if query_embedding:
            conditions.append("c.embedding IS NOT NULL")
            order = "c.embedding <=> :embedding"
            params["embedding"] = str(query_embedding)
        else:
            order = "c.updated_at DESC"

        sql = base
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        sql += f" ORDER BY {order} LIMIT :limit"

        result = await self.session.execute(text(sql), params)
        return result.scalars().all()

    async def search_cases_hybrid(
        self,
        query_embedding: list[float] | None = None,
        industry: str | None = None,
        city: str | None = None,
        limit: int = 20,
    ) -> Sequence[SuccessCase]:
        base = "SELECT sc.* FROM success_cases sc"
        conditions = []
        params: dict = {"limit": limit}

        if industry:
            conditions.append("sc.industry = :industry")
            params["industry"] = industry
        if city:
            conditions.append("sc.city = :city")
            params["city"] = city

        if query_embedding:
            conditions.append("sc.embedding IS NOT NULL")
            order = "sc.embedding <=> :embedding"
            params["embedding"] = str(query_embedding)
        else:
            order = "sc.created_at DESC"

        sql = base
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        sql += f" ORDER BY {order} LIMIT :limit"

        result = await self.session.execute(text(sql), params)
        return result.scalars().all()
