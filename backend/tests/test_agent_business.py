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
from app.domains.business.schemas import AgentActionLogResponse
from app.domains.business import service as business_service
from app.shared.schemas import PaginationParams
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
    assert captured["audit"]["status"] == "ok"


def test_agent_unsupported_action_is_audited_as_error(monkeypatch) -> None:
    audit_id = uuid4()
    captured = {}

    class FakeAuditService:
        def __init__(self, *_args, **_kwargs):
            pass

        async def log(self, **kwargs):
            captured["audit"] = kwargs
            return SimpleNamespace(id=audit_id)

    monkeypatch.setattr(agent_router, "AgentAuditService", lambda _db: FakeAuditService())

    request = AgentActionRequest(
        agent_name="openclaw",
        action="delete_everything",
        payload={"reason": "bad command"},
    )

    result = asyncio.run(agent_router.run_action(request, db=object()))

    assert result.code == 1
    assert result.data is None
    assert "Unsupported agent action" in result.message
    assert captured["audit"]["agent_name"] == "openclaw"
    assert captured["audit"]["action"] == "delete_everything"
    assert captured["audit"]["status"] == "error"
    assert captured["audit"]["result_json"]["error_type"] == "ValidationError"


def test_agent_graph_recall_action(monkeypatch) -> None:
    audit_id = uuid4()
    captured = {}

    class FakeGraphMemoryService:
        def __init__(self, *_args, **_kwargs):
            pass

        async def recall(self, body):
            captured["recall"] = body.model_dump()
            return SimpleNamespace(
                model_dump=lambda mode=None: {
                    "query_nodes": [],
                    "items": [],
                    "gate": {"mode": "graph_first"},
                }
            )

    class FakeAuditService:
        def __init__(self, *_args, **_kwargs):
            pass

        async def log(self, **kwargs):
            captured["audit"] = kwargs
            return SimpleNamespace(id=audit_id)

    monkeypatch.setattr(agent_router, "GraphMemoryService", FakeGraphMemoryService)
    monkeypatch.setattr(agent_router, "AgentAuditService", lambda _db: FakeAuditService())

    request = AgentActionRequest(
        agent_name="hermes",
        action="graph_recall",
        payload={"industry": "能源", "domain": "数据中台"},
    )

    result = asyncio.run(agent_router.run_action(request, db=object()))

    assert result.code == 0
    assert captured["recall"]["industry"] == "能源"
    assert captured["recall"]["domain"] == "数据中台"
    assert captured["audit"]["target_type"] == "graph_recall"
    assert captured["audit"]["status"] == "ok"


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


def test_list_agent_audit_logs_endpoint() -> None:
    audit_id = uuid4()
    now = datetime.now(timezone.utc)
    item = SimpleNamespace(
        id=audit_id,
        agent_name="hermes",
        action="create_engagement",
        target_type="engagement",
        target_id=uuid4(),
        request_json={"action": "create_engagement"},
        result_json={"name": "试点项目"},
        status="ok",
        created_at=now,
    )

    class FakeAuditRepository:
        async def get_filtered(self, pagination, **filters):
            assert pagination.page == 1
            assert filters == {
                "agent_name": "hermes",
                "action": None,
                "status": "ok",
                "target_type": "engagement",
            }
            return [item], 1

    result = asyncio.run(
        business_router.list_agent_audit_logs(
            agent_name="hermes",
            status="ok",
            target_type="engagement",
            pagination=PaginationParams(page=1, page_size=20),
            repo=FakeAuditRepository(),
        )
    )

    assert result.code == 0
    assert result.data.total == 1
    assert result.data.items[0].id == audit_id
    assert result.data.items[0].agent_name == "hermes"


def test_get_agent_audit_log_endpoint() -> None:
    audit_id = uuid4()
    now = datetime.now(timezone.utc)
    item = SimpleNamespace(
        id=audit_id,
        agent_name="openclaw",
        action="add_artifact",
        target_type="artifact",
        target_id=uuid4(),
        request_json={"action": "add_artifact"},
        result_json={"title": "合同范本"},
        status="ok",
        created_at=now,
    )

    class FakeAuditRepository:
        async def get_by_id(self, entity_id):
            assert entity_id == audit_id
            return item

    result = asyncio.run(
        business_router.get_agent_audit_log(audit_id, repo=FakeAuditRepository())
    )

    assert result.code == 0
    assert result.data == AgentActionLogResponse.model_validate(item)


def test_agent_audit_summary_endpoint() -> None:
    audit_id = uuid4()
    now = datetime.now(timezone.utc)
    error_item = SimpleNamespace(
        id=audit_id,
        agent_name="hermes",
        action="advance_stage",
        target_type="engagement",
        target_id=uuid4(),
        request_json={"action": "advance_stage"},
        result_json={"error": "stage is required"},
        status="error",
        created_at=now,
    )

    class FakeAuditRepository:
        async def get_summary(self):
            return {
                "status_counts": {"ok": 3, "error": 1},
                "action_counts": {"create_engagement": 2, "advance_stage": 1},
                "agent_counts": {"hermes": 4},
                "latest_errors": [error_item],
            }

    result = asyncio.run(
        business_router.summarize_agent_audit_logs(repo=FakeAuditRepository())
    )

    assert result.code == 0
    assert result.data.status_counts["error"] == 1
    assert result.data.latest_errors[0].status == "error"
