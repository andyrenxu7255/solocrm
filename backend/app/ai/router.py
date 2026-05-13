from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.client import AIClient
from app.ai.prompts import load_prompt
from app.database import get_db
from app.domains.case.models import SuccessCase
from app.domains.customer.meddic import MeddicReviewService
from app.domains.customer.models import Customer
from app.domains.customer.schemas import CustomerResponse
from app.shared.exceptions import NotFoundError
from app.shared.schemas import APIResponse

router = APIRouter(prefix="/ai", tags=["AI"])


class MeddicReviewRequest(BaseModel):
    customer_id: UUID


class OpeningRequest(BaseModel):
    customer_id: UUID
    case_id: UUID | None = Field(default=None, description="Optional matching success case")


@router.post("/meddic", response_model=APIResponse[CustomerResponse])
async def meddic_review(
    body: MeddicReviewRequest,
    db: AsyncSession = Depends(get_db),
):
    svc = MeddicReviewService(db)
    customer = await svc.review(body.customer_id)
    return APIResponse.ok(CustomerResponse.model_validate(customer))


@router.post("/opening", response_model=APIResponse[dict])
async def generate_opening(
    body: OpeningRequest,
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import select

    customer = (
        await db.execute(select(Customer).where(Customer.id == body.customer_id))
    ).scalar_one_or_none()
    if not customer:
        raise NotFoundError("Customer", str(body.customer_id))

    case = None
    if body.case_id:
        case = (
            await db.execute(select(SuccessCase).where(SuccessCase.id == body.case_id))
        ).scalar_one_or_none()

    context_parts = [
        f"客户姓名: {customer.name}",
        f"公司: {customer.company}",
        f"职位: {customer.title}",
        f"行业: {customer.industry}",
        f"城市: {customer.city}",
    ]
    if customer.notes:
        context_parts.append(f"备注: {customer.notes}")
    if customer.meddic_json:
        context_parts.append(f"MEDDIC评估: 健康分{customer.meddic_json.get('health_score','?')}/100")

    if case:
        context_parts.append(f"\n参考成功案例: {case.title} ({case.company_name}, {case.industry})")
        if case.summary:
            context_parts.append(f"案例摘要: {case.summary}")

    system_prompt = load_prompt("generate_opening")
    client = AIClient()
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "\n".join(context_parts)},
    ]
    response = await client.chat(messages, temperature=0.7, max_tokens=1024)

    return APIResponse.ok({"content": response, "customer_name": customer.name})


class IntelRequest(BaseModel):
    customer_id: UUID


@router.post("/intel", response_model=APIResponse[dict])
async def customer_intel(
    body: IntelRequest,
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import select

    customer = (
        await db.execute(select(Customer).where(Customer.id == body.customer_id))
    ).scalar_one_or_none()
    if not customer:
        raise NotFoundError("Customer", str(body.customer_id))

    if not customer.company:
        return APIResponse.ok({"results": [], "summary": "该客户没有公司信息"})

    from app.utils.web_search import search_company_news, format_news_for_prompt

    news = search_company_news(customer.company)
    context = format_news_for_prompt(customer.company, news)

    client = AIClient()
    messages = [
        {
            "role": "system",
            "content": "你是一个销售情报分析助手。根据提供的公司公开信息，提炼出对销售有用的洞察：近期动态、潜在需求、决策窗口。用简洁中文回答。",
        },
        {"role": "user", "content": context},
    ]
    summary = await client.chat(messages, temperature=0.3, max_tokens=512)

    return APIResponse.ok({"results": news, "summary": summary})
