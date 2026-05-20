from __future__ import annotations

import json
import uuid
from pathlib import Path

from fastapi import UploadFile

from app.ai.client import AIClient
from app.ai.fallbacks import fallback_visit_summary, has_llm_access
from app.ai.prompts import load_prompt
from app.domains.visit.models import VisitPlan, VisitRecord
from app.domains.visit.schemas import (
    VisitPlanCreate,
    VisitPlanUpdate,
    VisitRecordCreate,
    VisitRecordUpdate,
)
from app.shared.base_service import BaseService
from app.shared.exceptions import ExternalServiceError
from app.utils.speech import transcribe_audio

UPLOAD_DIR = Path("data/audio")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


class VisitPlanService(BaseService[VisitPlan]):
    async def create_from_schema(self, data: VisitPlanCreate) -> VisitPlan:
        instance = VisitPlan(**data.model_dump())
        return await self.repository.create(instance)

    async def update_from_schema(
        self, instance: VisitPlan, data: VisitPlanUpdate
    ) -> VisitPlan:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(instance, field, value)
        return await self.repository.update(instance)


class VisitRecordService(BaseService[VisitRecord]):
    async def create_from_schema(self, data: VisitRecordCreate) -> VisitRecord:
        instance = VisitRecord(**data.model_dump())
        return await self.repository.create(instance)

    async def update_from_schema(
        self, instance: VisitRecord, data: VisitRecordUpdate
    ) -> VisitRecord:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(instance, field, value)
        return await self.repository.update(instance)

    async def create_with_audio(
        self,
        data: VisitRecordCreate,
        audio_file: UploadFile | None = None,
    ) -> VisitRecord:
        instance = await self.create_from_schema(data)

        if audio_file:
            audio_path = UPLOAD_DIR / f"{instance.id}_{uuid.uuid4().hex[:8]}_{audio_file.filename}"
            content = await audio_file.read()
            audio_path.write_bytes(content)
            instance.audio_path = str(audio_path)

            try:
                transcript = await transcribe_audio(str(audio_path))
                instance.transcript = transcript.get("text", "")
                instance = await self.repository.update(instance)
            except Exception:
                pass

        return instance

    async def generate_ai_summary(self, record: VisitRecord) -> VisitRecord:
        if not record.transcript:
            return record

        parsed = None
        if has_llm_access():
            client = AIClient()
            system_prompt = load_prompt("visit_summary")
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": record.transcript},
            ]
            try:
                response = await client.chat(messages, temperature=0.3)
                parsed = _parse_json_response(response)
            except ExternalServiceError:
                parsed = None
        if not parsed:
            parsed = fallback_visit_summary(record.transcript)

        if parsed:
            record.summary = parsed.get("summary", "")
            record.key_people = parsed.get("key_people", [])
            record.action_items = parsed.get("action_items", [])
            record = await self.repository.update(record)

        return record


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
