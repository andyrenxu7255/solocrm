from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import UUID, uuid4

from sqlalchemy import MetaData
from sqlalchemy.dialects.postgresql import dialect
from sqlalchemy.schema import CreateTable

from app.domains.graph import repository as graph_repository
from app.domains.graph import router as graph_router
from app.domains.graph import service as graph_service
from app.domains.graph.schemas import (
    GraphEdgeResponse,
    GraphFactInput,
    GraphNodeResponse,
    GraphRecallRequest,
)
from app.shared.schemas import PaginationParams


NOW = datetime.now(timezone.utc)


def make_node(node_type: str, name: str, source_type: str = "", source_id=None):
    return SimpleNamespace(
        id=uuid4(),
        node_type=node_type,
        name=name,
        canonical_name=graph_service.canonicalize(name),
        description="",
        source_type=source_type,
        source_id=source_id,
        properties_json=None,
        created_at=NOW,
        updated_at=NOW,
    )


def make_edge(
    from_node,
    relation_type: str,
    to_node,
    source_type: str = "case",
    source_id: UUID | None = None,
    confidence: float = 0.9,
):
    return SimpleNamespace(
        id=uuid4(),
        from_node_id=from_node.id,
        relation_type=relation_type,
        to_node_id=to_node.id,
        weight=1.0,
        confidence=confidence,
        source_type=source_type,
        source_id=source_id or uuid4(),
        evidence="同行业同领域案例",
        properties_json=None,
        created_at=NOW,
        updated_at=NOW,
    )


def test_graph_recall_scores_shared_industry_and_domain(monkeypatch) -> None:
    industry = make_node("industry", "能源")
    domain = make_node("domain", "数据中台")
    case_id = uuid4()
    case_node = make_node("case", "北京电力数据中台", "case", case_id)
    edges = [
        make_edge(case_node, "in_industry", industry, source_id=case_id),
        make_edge(case_node, "serves_domain", domain, source_id=case_id),
    ]

    class FakeGraphMemoryService(graph_service.GraphMemoryService):
        def __init__(self):
            pass

        async def _resolve_query_nodes(self, _body):
            return [industry, domain]

        async def _candidate_source_edges(self, _touching_edges, _query_node_ids):
            return edges

        async def _node_map_for_edges(self, _edges):
            return {node.id: node for node in [industry, domain, case_node]}

        async def _load_source_records(
            self,
            _source_edges,
            _body,
            query_node_ids=None,
            node_map=None,
        ):
            return [
                graph_service.SourceRecord(
                    source_type="case",
                    source_id=case_id,
                    title="北京电力数据中台",
                    payload={
                        "title": "北京电力数据中台",
                        "summary": "能源行业数据中台项目",
                    },
                )
            ]

    svc = FakeGraphMemoryService()
    svc.edges = SimpleNamespace(edges_touching_nodes=lambda _ids: _async(edges))

    result = asyncio.run(
        svc.recall(GraphRecallRequest(industry="能源", domain="数据中台"))
    )

    assert result.gate["mode"] == "graph_first"
    assert result.items[0].target_type == "case"
    assert result.items[0].target_id == case_id
    assert result.items[0].score == 1.8
    assert {node.name for node in result.items[0].shared_nodes} == {"能源", "数据中台"}
    assert len(result.items[0].paths) == 2


def test_graph_recall_returns_empty_when_no_query_nodes() -> None:
    class FakeGraphMemoryService(graph_service.GraphMemoryService):
        def __init__(self):
            pass

        async def _resolve_query_nodes(self, _body):
            return []

    result = asyncio.run(
        FakeGraphMemoryService().recall(GraphRecallRequest(industry="未知行业"))
    )

    assert result.items == []
    assert result.gate["reason"] == "no query nodes matched"


def test_upsert_fact_endpoint() -> None:
    industry = make_node("industry", "能源")
    domain = make_node("domain", "数据中台")
    edge = make_edge(industry, "serves_domain", domain)

    class FakeMemoryService:
        async def upsert_fact(self, body):
            assert body.industry == "能源"
            return SimpleNamespace(
                nodes=[
                    GraphNodeResponse.model_validate(industry),
                    GraphNodeResponse.model_validate(domain),
                ],
                edges=[
                    GraphEdgeResponse.model_validate(edge),
                ],
            )

    result = asyncio.run(
        graph_router.upsert_fact(
            GraphFactInput(industry="能源", domain="数据中台"),
            svc=FakeMemoryService(),
        )
    )

    assert result.code == 0
    assert len(result.data.nodes) == 2
    assert len(result.data.edges) == 1


def test_graph_edge_identity_treats_missing_source_id_as_duplicate() -> None:
    metadata = MetaData()
    graph_service.GraphNode.__table__.to_metadata(metadata)
    table = graph_service.GraphEdge.__table__.to_metadata(metadata)
    ddl = str(CreateTable(table).compile(dialect=dialect()))

    assert "UNIQUE NULLS NOT DISTINCT" in ddl


def test_edges_for_sources_checks_both_edge_directions() -> None:
    statement = graph_repository.GraphEdgeRepository.edges_for_sources
    names = statement.__code__.co_names

    assert "from_node_id" in names
    assert "to_node_id" in names


def test_graph_edge_source_indexes_exist() -> None:
    index_names = {index.name for index in graph_service.GraphEdge.__table__.indexes}

    assert {
        "idx_graph_edges_from_node",
        "idx_graph_edges_to_node",
        "idx_graph_edges_source",
        "idx_graph_edges_relation",
    }.issubset(index_names)


def test_graph_node_lookup_indexes_exist() -> None:
    index_names = {index.name for index in graph_service.GraphNode.__table__.indexes}

    assert {
        "idx_graph_nodes_type",
        "idx_graph_nodes_source",
    }.issubset(index_names)


def test_candidate_edges_can_recall_customer_node_facts() -> None:
    industry = make_node("industry", "能源")
    customer = make_node("customer", "北京电力")
    domain = make_node("domain", "数据中台")
    edges = [
        make_edge(customer, "in_industry", industry, source_type="agent"),
        make_edge(customer, "serves_domain", domain, source_type="agent"),
    ]
    for edge in edges:
        edge.source_id = None

    class FakeEdgeRepository:
        async def edges_for_sources(self, source_ids):
            assert source_ids == [customer.id]
            return edges

    svc = graph_service.GraphMemoryService.__new__(graph_service.GraphMemoryService)
    svc.edges = FakeEdgeRepository()
    svc.session = None

    result = asyncio.run(
        svc._candidate_source_edges(
            touching_edges=[edges[0]],
            query_node_ids=[industry.id],
        )
    )

    assert {edge.id for edge in result} == {edge.id for edge in edges}


def test_list_nodes_endpoint() -> None:
    industry = make_node("industry", "能源")

    class FakeRepository:
        async def list_filtered(self, pagination, node_type, q):
            assert pagination.page == 1
            assert node_type == "industry"
            assert q == "能"
            return [industry], 1

    fake_service = SimpleNamespace(repository=FakeRepository())
    result = asyncio.run(
        graph_router.list_nodes(
            node_type="industry",
            q="能",
            pagination=PaginationParams(page=1, page_size=20),
            svc=fake_service,
        )
    )

    assert result.code == 0
    assert result.data.items[0].name == "能源"


async def _async(value):
    return value
