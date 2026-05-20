from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.ai import embedding
from app.domains.agent import router as agent_router
from app.domains.agent.schemas import AgentActionRequest
from app.domains.business import router as business_router
from app.domains.business import service as business_service
from app.shared.exceptions import ValidationError


def test_validate_stage_rejects_bad_stage() -> None:
    with pytest.raises(ValidationError):
        business_service._validate_stage("prototype")


def test_generate_embedding_offline_returns_empty_list(monkeypatch) -> None:
    monkeypatch.setattr(
        embedding,
        "get_settings",
        lambda: SimpleNamespace(openai_api_key=""),
    )

    def _boom():
        raise AssertionError("_get_client should not be called without an API key")

    monkeypatch.setattr(embedding, "_get_client", _boom)

    assert asyncio.run(embedding.generate_embedding("hello")) == []
    assert asyncio.run(embedding.generate_embeddings(["a", "b"])) == [[], []]


def test_agent_create_engagement_action(monkeypatch) -> None:
    engagement_id = uuid4()
    audit_id = uuid4()
    now = datetime.now(timezone.utc)
    captured = {}

    fake_engagement = SimpleNamespace(
        id=engagement_id,
        customer_id=None,
        name="试点项目",
        company="星海科技",
        stage="sales",
        status="active",
        owner="Andy",
        value=120000.0,
        close_date=None,
        priority=2,
        sales_json={"source": "wechat"},
        presales_json=None,
        delivery_json=None,
        next_actions=[{"title": "约电话", "status": "open"}],
        risks=[],
        tags=["pilot"],
        created_at=now,
        updated_at=now,
    )

    class FakeEngagementService:
        def __init__(self, *_args, **_kwargs):
            self.repository = SimpleNamespace(get_by_id=self.get_by_id)

        async def create_from_schema(self, data):
            captured["engagement"] = data.model_dump()
            return fake_engagement

        async def get_by_id(self, _entity_id):
            return fake_engagement

        async def update_from_schema(self, _instance, data):
            captured["update"] = data.model_dump(exclude_unset=True)
            return fake_engagement

    class FakeAuditService:
        def __init__(self, *_args, **_kwargs):
            pass

        async def log(self, **kwargs):
            captured["audit"] = kwargs
            return SimpleNamespace(id=audit_id)

    monkeypatch.setattr(agent_router, "engagement_service", lambda _db: FakeEngagementService())
    monkeypatch.setattr(agent_router, "artifact_service", lambda _db: None)
    monkeypatch.setattr(agent_router, "BusinessReadService", lambda _db: None)
    monkeypatch.setattr(agent_router, "AgentAuditService", lambda _db: FakeAuditService())

    request = AgentActionRequest(
        agent_name="hermes",
        action="create_engagement",
        payload={
            "name": "试点项目",
            "company": "星海科技",
            "stage": "sales",
            "status": "active",
            "owner": "Andy",
            "priority": 2,
            "value": 120000,
            "tags": ["pilot"],
        },
    )

    result = asyncio.run(agent_router.run_action(request, db=object()))

    assert result.code == 0
    assert result.data.action == "create_engagement"
    assert result.data.target_type == "engagement"
    assert result.data.target_id == str(engagement_id)
    assert result.data.result["name"] == "试点项目"
    assert captured["engagement"]["name"] == "试点项目"
    assert captured["audit"]["agent_name"] == "hermes"


def test_business_export_endpoint(monkeypatch) -> None:
    expected = {
        "format": "solocrm-agent-context-v1",
        "tables": {"customers": [{"id": "c-1"}]},
    }

    class FakeReadService:
        def __init__(self, *_args, **_kwargs):
            pass

        async def export_agent_context(self):
            return expected

    monkeypatch.setattr(business_router, "BusinessReadService", FakeReadService)

    result = asyncio.run(business_router.business_export(db=object()))

    assert result.code == 0
    assert result.data == expected


def test_business_summary_endpoint(monkeypatch) -> None:
    expected = {"stages": {"sales": 2}, "active_engagements": 1, "open_risks": 0, "next_actions": [], "artifact_types": {}}

    class FakeReadService:
        def __init__(self, *_args, **_kwargs):
            pass

        async def summarize_pipeline(self):
            return business_service.PipelineSummary(**expected)

    monkeypatch.setattr(business_router, "BusinessReadService", FakeReadService)

    result = asyncio.run(business_router.business_summary(db=object()))

    assert result.code == 0
    assert result.data.active_engagements == 1
