from __future__ import annotations

import json
import uuid
from datetime import date, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.client import AIClient
from app.ai.fallbacks import fallback_meddic_review, has_llm_access
from app.ai.prompts import load_prompt
from app.domains.customer.models import Customer
from app.domains.todo.models import Todo
from app.domains.visit.models import VisitRecord
from app.shared.exceptions import ExternalServiceError
from app.shared.exceptions import NotFoundError


class MeddicReviewService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def review(self, customer_id: uuid.UUID) -> Customer:
        from sqlalchemy import select, desc

        customer = (
            await self.session.execute(
                select(Customer).where(Customer.id == customer_id)
            )
        ).scalar_one_or_none()

        if not customer:
            raise NotFoundError("Customer", str(customer_id))

        recent_records = (
            await self.session.execute(
                select(VisitRecord)
                .where(VisitRecord.customer_id == customer_id)
                .order_by(desc(VisitRecord.visit_date))
                .limit(5)
            )
        ).scalars().all()

        context = _build_context(customer, recent_records)
        system_prompt = load_prompt("meddic_review")

        result = None
        if has_llm_access():
            client = AIClient()
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": context},
            ]
            try:
                response = await client.chat(messages, temperature=0.3)
                result = _parse_json_response(response)
            except ExternalServiceError:
                result = None
        if not result:
            result = fallback_meddic_review(customer, recent_records)

        if result:
            customer.meddic_json = {
                "metrics": result.get("metrics", {}),
                "economic_buyer": result.get("economic_buyer", {}),
                "decision_criteria": result.get("decision_criteria", {}),
                "decision_process": result.get("decision_process", {}),
                "pain_points": result.get("pain_points", {}),
                "champion": result.get("champion", {}),
                "health_score": result.get("health_score", 0),
                "gaps": result.get("overall_gaps", []),
                "last_review_at": datetime.utcnow().isoformat(),
            }
            await self.session.flush()

            actions = result.get("recommended_actions", [])
            for i, action in enumerate(actions):
                todo = Todo(
                    customer_id=customer.id,
                    title=str(action)[:300],
                    priority=i + 1,
                    meddic_dim=_guess_dimension(str(action)),
                    source="meddic_review",
                    status="pending",
                )
                self.session.add(todo)

            await self.session.flush()

        return customer


def _build_context(customer: Customer, records: list[VisitRecord]) -> str:
    parts = [
        f"客户: {customer.name}",
        f"公司: {customer.company}",
        f"行业: {customer.industry}",
        f"城市: {customer.city}",
        f"当前状态: {customer.status}",
    ]

    if customer.notes:
        parts.append(f"备注: {customer.notes}")
    if customer.meddic_json:
        parts.append(f"历史MEDDIC: {json.dumps(customer.meddic_json, ensure_ascii=False)}")

    if records:
        parts.append(f"\n最近{len(records)}次拜访记录:")
        for r in records:
            parts.append(f"- {r.visit_date.isoformat()}: {r.summary or r.transcript or r.raw_notes}")

    return "\n".join(parts)


def _guess_dimension(action: str) -> str:
    mapping = {
        "指标": "metrics",
        "roi": "metrics",
        "经济": "economic_buyer",
        "决策": "decision_criteria",
        "标准": "decision_criteria",
        "流程": "decision_process",
        "痛点": "pain_points",
        "痛苦": "pain_points",
        "支持者": "champion",
        "champion": "champion",
    }
    action_lower = action.lower()
    for kw, dim in mapping.items():
        if kw.lower() in action_lower:
            return dim
    return ""


def _parse_json_response(text: str) -> dict | None:
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        try:
            start = text.index("{")
            end = text.rindex("}") + 1
            return json.loads(text[start:end])
        except (ValueError, json.JSONDecodeError):
            return None
