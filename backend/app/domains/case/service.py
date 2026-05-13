from __future__ import annotations

import json

from app.ai.client import AIClient
from app.ai.embedding import generate_embedding
from app.ai.prompts import load_prompt
from app.domains.case.models import SuccessCase
from app.domains.case.schemas import CaseCreate, CaseUpdate
from app.shared.base_service import BaseService


class CaseService(BaseService[SuccessCase]):
    async def create_from_schema(self, data: CaseCreate) -> SuccessCase:
        instance = SuccessCase(**data.model_dump())

        text = _case_to_text(data)
        if text:
            instance.embedding = await generate_embedding(text)

        return await self.repository.create(instance)

    async def update_from_schema(
        self, instance: SuccessCase, data: CaseUpdate
    ) -> SuccessCase:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(instance, field, value)

        text = _case_instance_to_text(instance)
        if text:
            instance.embedding = await generate_embedding(text)

        return await self.repository.update(instance)

    async def extract_from_conversation(self, user_input: str) -> SuccessCase:
        client = AIClient()
        system_prompt = load_prompt("case_extraction")
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input},
        ]
        response = await client.chat(messages, temperature=0.3)
        extracted = _parse_json_response(response)

        if not extracted:
            create_data = CaseCreate(
                title=user_input[:200],
                company_name="",
                industry="",
                summary=user_input,
            )
        else:
            create_data = CaseCreate(
                title=extracted.get("title", user_input[:200]),
                company_name=extracted.get("company_name", ""),
                industry=extracted.get("industry", ""),
                city=extracted.get("city", ""),
                product=extracted.get("product", ""),
                deal_size=extracted.get("deal_size"),
                summary=extracted.get("summary", user_input),
                key_points=extracted.get("key_points"),
            )

        return await self.create_from_schema(create_data)


def _case_to_text(data: CaseCreate) -> str:
    parts = [
        data.title,
        data.company_name,
        data.industry,
        data.city,
        data.product,
        data.summary,
    ]
    if data.key_points:
        parts.append(" ".join(
            f"{kp.get('key', '')}: {kp.get('value', '')}" for kp in data.key_points
        ))
    return " ".join(p for p in parts if p)


def _case_instance_to_text(instance: SuccessCase) -> str:
    parts = [
        instance.title,
        instance.company_name,
        instance.industry,
        instance.city,
        instance.product,
        instance.summary or "",
    ]
    if instance.key_points:
        parts.append(" ".join(
            f"{kp.get('key', '')}: {kp.get('value', '')}" for kp in instance.key_points
        ))
    return " ".join(p for p in parts if p)


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
