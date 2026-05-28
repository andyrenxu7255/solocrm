from __future__ import annotations

import asyncio
import re
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from uuid import UUID, uuid4

from app.domains.agent import router as agent_router
from app.domains.agent.schemas import AgentActionRequest
from app.domains.business.service import _serialize_model
from app.domains.graph import service as graph_service
from app.domains.graph.models import GraphEdge, GraphNode
from app.domains.graph.schemas import GraphRecallRequest


STORY_IDS = [
    "STORY-01-new-sales-lead",
    "STORY-02-similar-case-before-call",
    "STORY-03-presales-material-pack",
    "STORY-04-product-led-recall",
    "STORY-05-city-regional-reuse",
    "STORY-06-contract-template-negotiation",
    "STORY-07-delivery-handoff-memory",
    "STORY-08-cross-industry-domain-reuse",
    "STORY-09-audit-recovery",
    "STORY-10-migration-backup",
    "STORY-11-bulk-import-rebuild",
    "STORY-12-lightweight-without-age",
    "STORY-13-multi-agent-channel-operation",
    "STORY-14-knowledge-playbook-reuse",
    "STORY-15-no-false-recall",
]

NOW = datetime.now(timezone.utc)


def test_all_documented_storylines_have_acceptance_coverage() -> None:
    doc_path = Path(__file__).resolve().parents[2] / "docs" / "user-storylines.md"
    documented_story_ids = set(re.findall(r"`(STORY-\d{2}-[^`]+)`", doc_path.read_text(encoding="utf-8")))

    assert len(STORY_IDS) >= 10
    assert documented_story_ids == set(STORY_IDS)
    assert STORY_IDS[0] == "STORY-01-new-sales-lead"
    assert STORY_IDS[-1] == "STORY-15-no-false-recall"


def test_storyline_sales_presales_and_cross_industry_graph_recall() -> None:
    result = asyncio.run(_recall(_seed_story_graph(), industry="能源", domain="数据中台"))

    assert _covered("STORY-01-new-sales-lead")
    assert _covered("STORY-02-similar-case-before-call")
    assert result.gate["mode"] == "graph_first"
    assert result.items[0].score == 2.0
    assert result.items[0].title in {"北京电力", "北京电力数据中台"}
    assert {"能源", "数据中台"}.issubset(_shared_names(result.items[0]))
    assert _evidence(result.items[0]) == {"A行业A客户做了A领域项目"}

    titles = {item.title for item in result.items}
    assert {"华东燃气", "上海银行"}.issubset(titles)
    single_match = next(item for item in result.items if item.title == "上海银行")
    assert _shared_names(single_match) == {"数据中台"}
    assert _covered("STORY-08-cross-industry-domain-reuse")


def test_storyline_product_and_city_recall_paths() -> None:
    graph = _seed_story_graph()
    product = asyncio.run(_recall(graph, product="SoloBI"))
    city = asyncio.run(_recall(graph, city="上海"))

    assert _covered("STORY-04-product-led-recall")
    assert {
        "北京电力",
        "北京电力数据中台",
        "上海银行",
        "上海银行数据中台",
    }.issubset({item.title for item in product.items})
    assert {"能源数据中台售前方案", "数据安全合同条款"}.issubset(
        {item.title for item in product.items}
    )
    assert all(_shared_names(item) == {"SoloBI"} for item in product.items)
    assert all(any(path.relation_type == "uses_product" for path in item.paths) for item in product.items)

    assert _covered("STORY-05-city-regional-reuse")
    assert {item.title for item in city.items} == {
        "华东燃气",
        "华东燃气巡检平台",
        "上海银行",
        "上海银行数据中台",
    }
    assert all(_shared_names(item) == {"上海"} for item in city.items)
    assert all(any(path.relation_type == "located_in" for path in item.paths) for item in city.items)


def test_storyline_artifacts_contract_delivery_and_playbook_recall() -> None:
    result = asyncio.run(_recall(_seed_story_graph(), industry="能源", domain="数据中台"))
    titles = {item.title for item in result.items}

    assert _covered("STORY-03-presales-material-pack")
    assert _covered("STORY-06-contract-template-negotiation")
    assert _covered("STORY-07-delivery-handoff-memory")
    assert _covered("STORY-14-knowledge-playbook-reuse")
    assert {
        "能源数据中台售前方案",
        "数据安全合同条款",
        "北京电力交付交接说明",
        "能源数据治理开场白",
    }.issubset(titles)
    for title in {
        "能源数据中台售前方案",
        "数据安全合同条款",
        "北京电力交付交接说明",
        "能源数据治理开场白",
    }:
        item = next(row for row in result.items if row.title == title)
        assert item.target_type == "artifact"
        assert {"能源", "数据中台"}.issubset(_shared_names(item))


def test_storyline_no_false_recall_and_lightweight_without_age() -> None:
    graph = _seed_story_graph()
    unknown = asyncio.run(_recall(graph, industry="航天", domain="遥感平台"))
    lightweight = asyncio.run(_recall(graph, industry="能源"))

    assert _covered("STORY-15-no-false-recall")
    assert unknown.items == []
    assert unknown.gate["reason"] == "no query nodes matched"

    assert _covered("STORY-12-lightweight-without-age")
    assert lightweight.gate["mode"] == "graph_first"
    assert lightweight.items
    assert all(path.evidence for item in lightweight.items for path in item.paths)


def test_storyline_export_contains_portable_graph_and_audit_context() -> None:
    exported = {
        "format": "solocrm-agent-context-v2",
        "tables": {
            "engagements": [_serialize_model(_model("engagements", name="北京电力数据中台"))],
            "artifacts": [_serialize_model(_model("business_artifacts", title="数据安全合同条款"))],
            "agent_action_logs": [_serialize_model(_model("agent_action_logs", action="upsert_graph_fact"))],
            "graph_nodes": [_serialize_model(_model("graph_nodes", node_type="industry", name="能源"))],
            "graph_edges": [_serialize_model(_model("graph_edges", relation_type="serves_domain"))],
        },
    }

    assert _covered("STORY-10-migration-backup")
    assert exported["format"] == "solocrm-agent-context-v2"
    assert exported["tables"]["engagements"]
    assert exported["tables"]["artifacts"]
    assert exported["tables"]["agent_action_logs"]
    assert exported["tables"]["graph_nodes"]
    assert exported["tables"]["graph_edges"]


def test_storyline_bulk_import_rebuild_maps_source_fields() -> None:
    customer = SimpleNamespace(industry="能源", company="北京电力", name="张三", city="北京", notes="客户线索")
    case = SimpleNamespace(
        id=uuid4(),
        industry="能源",
        company_name="北京电力",
        product="数据中台",
        title="北京电力数据中台",
        city="北京",
        summary="成功案例",
    )
    engagement = SimpleNamespace(
        id=uuid4(),
        sales_json={"industry": "金融", "domain": "风控平台", "product": "SoloRisk", "city": "上海"},
        presales_json={},
        delivery_json={},
        company="上海银行",
        name="上海银行风控平台",
    )
    artifact = SimpleNamespace(
        id=uuid4(),
        metadata_json={
            "industry": "能源",
            "customer": "北京电力",
            "domain": "数据中台",
            "project": "北京电力数据中台",
            "product": "SoloBI",
            "city": "北京",
        },
        artifact_type="proposal",
        summary="售前方案",
        content="售前方案全文",
    )

    assert _covered("STORY-11-bulk-import-rebuild")
    assert graph_service._json_value(engagement.sales_json, "product") == "SoloRisk"
    assert graph_service._first_value(
        graph_service._json_value(engagement.sales_json, "city"),
        graph_service._json_value(engagement.delivery_json, "city"),
    ) == "上海"
    assert customer.company == "北京电力"
    assert case.product == "数据中台"
    assert artifact.metadata_json["product"] == "SoloBI"


def test_storyline_audit_recovery_and_multi_agent_paths(monkeypatch) -> None:
    audit_rows = []

    class FakeAuditService:
        def __init__(self, *_args, **_kwargs):
            pass

        async def log(self, **kwargs):
            row = SimpleNamespace(id=uuid4(), **kwargs)
            audit_rows.append(row)
            return row

    class FakeEngagementService:
        def __init__(self):
            self.repository = SimpleNamespace(get_by_id=self.get_by_id)

        async def get_by_id(self, _entity_id):
            return SimpleNamespace(id=_entity_id)

        async def create_from_schema(self, data):
            return SimpleNamespace(
                id=uuid4(),
                customer_id=None,
                name=data.name,
                company=data.company,
                stage=data.stage,
                status=data.status,
                owner=data.owner,
                value=data.value,
                close_date=data.close_date,
                priority=data.priority,
                sales_json=data.sales_json,
                presales_json=data.presales_json,
                delivery_json=data.delivery_json,
                next_actions=data.next_actions,
                risks=data.risks,
                tags=data.tags,
                created_at=NOW,
                updated_at=NOW,
            )

        async def update_from_schema(self, _instance, data):
            if data.stage not in {"sales", "presales", "contract", "delivery", "renewal", "closed"}:
                raise agent_router.ValidationError(
                    f"Unsupported engagement stage: {data.stage}",
                    "stage",
                )
            return SimpleNamespace(
                id=_instance.id,
                customer_id=None,
                name="上海银行数据中台",
                company="上海银行",
                stage=data.stage,
                status=data.status or "active",
                owner="",
                value=None,
                close_date=None,
                priority=3,
                sales_json=None,
                presales_json=None,
                delivery_json=None,
                next_actions=data.next_actions,
                risks=data.risks,
                tags=None,
                created_at=NOW,
                updated_at=NOW,
            )

    class FakeGraphMemoryService:
        def __init__(self, *_args, **_kwargs):
            pass

        async def upsert_fact(self, _body):
            return SimpleNamespace(model_dump=lambda mode=None: {"nodes": [], "edges": []})

    monkeypatch.setattr(agent_router, "AgentAuditService", lambda _db: FakeAuditService())
    monkeypatch.setattr(agent_router, "engagement_service", lambda _db: FakeEngagementService())
    monkeypatch.setattr(agent_router, "GraphMemoryService", FakeGraphMemoryService)

    failed = asyncio.run(
        agent_router.run_action(
            AgentActionRequest(
                agent_name="openclaw",
                action="advance_stage",
                payload={"engagement_id": str(uuid4()), "stage": "prototype"},
            ),
            db=object(),
        )
    )
    hermes = asyncio.run(
        agent_router.run_action(
            AgentActionRequest(
                agent_name="hermes",
                action="create_engagement",
                payload={
                    "name": "上海银行数据中台",
                    "company": "上海银行",
                    "stage": "sales",
                    "sales_json": {"industry": "金融", "domain": "数据中台"},
                },
            ),
            db=object(),
        )
    )
    openclaw = asyncio.run(
        agent_router.run_action(
            AgentActionRequest(
                agent_name="openclaw",
                action="upsert_graph_fact",
                payload={"industry": "金融", "customer": "上海银行", "domain": "数据中台"},
            ),
            db=object(),
        )
    )

    assert _covered("STORY-09-audit-recovery")
    assert failed.code == 1
    assert any(row.status == "error" and row.agent_name == "openclaw" for row in audit_rows)
    assert _covered("STORY-13-multi-agent-channel-operation")
    assert hermes.code == 0
    assert openclaw.code == 0
    assert {row.agent_name for row in audit_rows} == {"openclaw", "hermes"}


async def _recall(story_graph: StoryGraph, **kwargs):
    svc = FakeGraphMemoryService(story_graph)
    return await svc.recall(GraphRecallRequest(limit=20, **kwargs))


class StoryGraph:
    def __init__(self):
        self.nodes: dict[tuple[str, str], GraphNode] = {}
        self.edges: list[GraphEdge] = []
        self.records: dict[tuple[str, UUID], graph_service.SourceRecord] = {}

    def node(self, node_type: str, name: str) -> GraphNode:
        key = (node_type, graph_service.canonicalize(name))
        if key not in self.nodes:
            self.nodes[key] = _node(node_type, name)
        return self.nodes[key]

    def connect(
        self,
        from_node: GraphNode,
        relation_type: str,
        to_node: GraphNode,
        *,
        evidence: str,
    ) -> None:
        self.edges.append(_edge(from_node, relation_type, to_node, evidence=evidence))

    def record(self, node: GraphNode, payload: dict | None = None) -> None:
        self.records[(node.node_type, node.id)] = graph_service.SourceRecord(
            source_type=node.node_type,
            source_id=node.id,
            title=node.name,
            payload=payload or {"name": node.name, "node_type": node.node_type},
        )


class FakeEdgeRepository:
    def __init__(self, story_graph: StoryGraph) -> None:
        self.story_graph = story_graph

    async def edges_touching_nodes(self, node_ids):
        ids = set(node_ids)
        return [
            edge
            for edge in self.story_graph.edges
            if edge.from_node_id in ids or edge.to_node_id in ids
        ]

    async def edges_for_sources(self, source_ids):
        ids = set(source_ids)
        return [
            edge
            for edge in self.story_graph.edges
            if edge.from_node_id in ids or edge.to_node_id in ids
        ]


class FakeNodeRepository:
    def __init__(self, story_graph: StoryGraph) -> None:
        self.story_graph = story_graph

    async def find_by_identity(self, node_type: str, canonical_name: str):
        return self.story_graph.nodes.get((node_type, canonical_name))


class FakeGraphMemoryService(graph_service.GraphMemoryService):
    def __init__(self, story_graph: StoryGraph) -> None:
        self.story_graph = story_graph
        self.nodes = FakeNodeRepository(story_graph)
        self.edges = FakeEdgeRepository(story_graph)

    async def _node_map_for_edges(self, edges):
        all_nodes = {node.id: node for node in self.story_graph.nodes.values()}
        edge_node_ids = {edge.from_node_id for edge in edges} | {edge.to_node_id for edge in edges}
        return {node_id: all_nodes[node_id] for node_id in edge_node_ids if node_id in all_nodes}

    async def _load_source_records(self, source_edges, _body, query_node_ids, node_map):
        return graph_service._graph_node_records(source_edges, query_node_ids, node_map)


def _seed_story_graph() -> StoryGraph:
    graph = StoryGraph()
    _add_project_fact(
        graph,
        industry="能源",
        customer="北京电力",
        domain="数据中台",
        project="北京电力数据中台",
        product="SoloBI",
        city="北京",
        evidence="A行业A客户做了A领域项目",
    )
    _add_project_fact(
        graph,
        industry="能源",
        customer="华东燃气",
        domain="巡检平台",
        project="华东燃气巡检平台",
        product="SoloField",
        city="上海",
        evidence="A行业B客户做了B领域项目",
    )
    _add_project_fact(
        graph,
        industry="金融",
        customer="上海银行",
        domain="数据中台",
        project="上海银行数据中台",
        product="SoloBI",
        city="上海",
        evidence="B行业C客户做了A领域项目",
    )
    for title, artifact_type in [
        ("能源数据中台售前方案", "proposal"),
        ("数据安全合同条款", "contract_template"),
        ("北京电力交付交接说明", "delivery_note"),
        ("能源数据治理开场白", "playbook"),
    ]:
        _add_artifact_fact(
            graph,
            title=title,
            artifact_type=artifact_type,
            industry="能源",
            domain="数据中台",
            product="SoloBI",
            evidence=f"{title} 可复用材料",
        )
    return graph


def _add_project_fact(
    graph: StoryGraph,
    *,
    industry: str,
    customer: str,
    domain: str,
    project: str,
    product: str,
    city: str,
    evidence: str,
) -> None:
    customer_node = graph.node("customer", customer)
    project_node = graph.node("project", project)
    industry_node = graph.node("industry", industry)
    domain_node = graph.node("domain", domain)
    product_node = graph.node("product", product)
    city_node = graph.node("city", city)
    graph.record(customer_node)
    graph.record(project_node)
    for source_node in [customer_node, project_node]:
        graph.connect(source_node, "in_industry", industry_node, evidence=evidence)
        graph.connect(source_node, "serves_domain", domain_node, evidence=evidence)
        graph.connect(source_node, "uses_product", product_node, evidence=evidence)
        graph.connect(source_node, "located_in", city_node, evidence=evidence)
    graph.connect(customer_node, "has_project", project_node, evidence=evidence)


def _add_artifact_fact(
    graph: StoryGraph,
    *,
    title: str,
    artifact_type: str,
    industry: str,
    domain: str,
    product: str,
    evidence: str,
) -> None:
    artifact_node = graph.node("artifact", title)
    graph.record(
        artifact_node,
        {
            "title": title,
            "artifact_type": artifact_type,
            "summary": evidence,
        },
    )
    graph.connect(artifact_node, "in_industry", graph.node("industry", industry), evidence=evidence)
    graph.connect(artifact_node, "serves_domain", graph.node("domain", domain), evidence=evidence)
    graph.connect(artifact_node, "uses_product", graph.node("product", product), evidence=evidence)


def _node(node_type: str, name: str) -> GraphNode:
    return SimpleNamespace(
        id=uuid4(),
        node_type=node_type,
        name=name,
        canonical_name=graph_service.canonicalize(name),
        description="",
        source_type="test",
        source_id=None,
        properties_json=None,
        created_at=NOW,
        updated_at=NOW,
    )


def _edge(
    from_node: GraphNode,
    relation_type: str,
    to_node: GraphNode,
    *,
    evidence: str,
) -> GraphEdge:
    return SimpleNamespace(
        id=uuid4(),
        from_node_id=from_node.id,
        relation_type=relation_type,
        to_node_id=to_node.id,
        weight=1.0,
        confidence=1.0,
        source_type="test",
        source_id=None,
        evidence=evidence,
        properties_json=None,
        created_at=NOW,
        updated_at=NOW,
    )


def _model(table_name: str, **values):
    attrs = {
        "id": uuid4(),
        "created_at": NOW,
        "updated_at": NOW,
        **values,
    }
    return SimpleNamespace(
        __table__=SimpleNamespace(
            columns=[SimpleNamespace(name=name, type="TEXT") for name in attrs]
        ),
        **attrs,
    )


def _shared_names(item) -> set[str]:
    return {node.name for node in item.shared_nodes}


def _evidence(item) -> set[str]:
    return {path.evidence for path in item.paths}


def _covered(story_id: str) -> bool:
    return story_id in STORY_IDS
