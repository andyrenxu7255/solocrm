from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.embedding import generate_embedding
from app.database import get_db
from app.domains.case.schemas import CaseResponse
from app.domains.customer.schemas import CustomerResponse
from app.domains.search.hybrid import HybridSearchService
from app.shared.schemas import APIResponse

router = APIRouter(prefix="/search", tags=["Search"])


class SearchRequest(BaseModel):
    industry: str | None = None
    city: str | None = None
    query: str | None = Field(default=None, description="Natural language search query for vector matching")
    limit: int = Field(default=20, ge=1, le=100)


@router.post("/customers", response_model=APIResponse[list[CustomerResponse]])
async def search_customers(
    body: SearchRequest,
    db: AsyncSession = Depends(get_db),
):
    svc = HybridSearchService(db)
    embedding = None
    if body.query:
        embedding = await generate_embedding(body.query)
    items = await svc.search_customers_hybrid(
        query_embedding=embedding,
        industry=body.industry,
        city=body.city,
        limit=body.limit,
    )
    return APIResponse.ok([CustomerResponse.model_validate(i) for i in items])


@router.post("/cases", response_model=APIResponse[list[CaseResponse]])
async def search_cases(
    body: SearchRequest,
    db: AsyncSession = Depends(get_db),
):
    svc = HybridSearchService(db)
    embedding = None
    if body.query:
        embedding = await generate_embedding(body.query)
    items = await svc.search_cases_hybrid(
        query_embedding=embedding,
        industry=body.industry,
        city=body.city,
        limit=body.limit,
    )
    return APIResponse.ok([CaseResponse.model_validate(i) for i in items])
