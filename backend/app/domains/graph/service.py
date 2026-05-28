from __future__ import annotations

import re
from collections import defaultdict
from copy import copy
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.business.models import BusinessArtifact, Engagement
from app.domains.case.models import SuccessCase
from app.domains.customer.models import Customer
from app.domains.graph.models import GraphEdge, GraphNode
from app.domains.graph.repository import GraphEdgeRepository, GraphNodeRepository
from app.domains.graph.schemas import (
    GRAPH_NODE_TYPES,
    GRAPH_RELATION_TYPES,
    GraphEdgeCreate,
    GraphEdgeResponse,
    GraphFactInput,
    GraphFactResponse,
    GraphNodeCreate,
    GraphNodeResponse,
    GraphPathStep,
    GraphRecallItem,
    GraphRecallRequest,
    GraphRecallResponse,
)
from app.shared.base_service import BaseService
from app.shared.exceptions import ValidationError


class GraphNodeService(BaseService[GraphNode]):
    repository: GraphNodeRepository

    async def create_from_schema(self, data: GraphNodeCreate) -> GraphNode:
        _validate_node_type(data.node_type)
        return await self.repository.upsert_node(
            node_type=data.node_type,
            name=data.name.strip(),
            canonical_name=canonicalize(data.name),
            description=data.description,
            source_type=data.source_type,
            source_id=data.source_id,
            properties_json=data.properties_json,
        )


class GraphEdgeService(BaseService[GraphEdge]):
    repository: GraphEdgeRepository

    async def create_from_schema(self, data: GraphEdgeCreate) -> GraphEdge:
        _validate_relation_type(data.relation_type)
        return await self.repository.upsert_edge(**data.model_dump())


@dataclass
class SourceRecord:
    source_type: str
    source_id: UUID
    title: str
    payload: dict


@dataclass(frozen=True)
class GraphRecallPolicy:
    default_max_hops: int = 1
    max_allowed_hops: int = 2
    bridge_decay: float = 0.55
    max_edges_per_bridge_node: int = 50
    allowed_recall_relations: frozenset[str] = frozenset(
        {
            "in_industry",
            "serves_domain",
            "uses_product",
            "located_in",
            "has_project",
            "has_case",
            "supports_artifact",
            "references",
        }
    )
    bridge_relations: frozenset[str] = frozenset(
        {
            "in_industry",
            "serves_domain",
            "uses_product",
            "located_in",
        }
    )
    result_node_types: frozenset[str] = frozenset(
        {"customer", "project", "case", "engagement", "artifact"}
    )


DEFAULT_RECALL_POLICY = GraphRecallPolicy()


class GraphMemoryService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.nodes = GraphNodeRepository(session)
        self.edges = GraphEdgeRepository(session)
        self.recall_policy = DEFAULT_RECALL_POLICY

    async def upsert_fact(self, fact: GraphFactInput) -> GraphFactResponse:
        if not any(
            [
                fact.industry,
                fact.customer,
                fact.domain,
                fact.project,
                fact.product,
                fact.city,
                fact.case_id,
                fact.engagement_id,
                fact.artifact_id,
            ]
        ):
            raise ValidationError("Graph fact must include at least one node", "fact")

        created_nodes: list[GraphNode] = []
        created_edges: list[GraphEdge] = []
        source_type, source_id = _source_from_fact(fact)

        customer_node = await self._maybe_node(
            "customer", fact.customer, source_type, source_id
        )
        industry_node = await self._maybe_node(
            "industry", fact.industry, source_type, source_id
        )
        domain_node = await self._maybe_node(
            "domain", fact.domain, source_type, source_id
        )
        project_node = await self._maybe_node(
            "project", fact.project, source_type, source_id
        )
        product_node = await self._maybe_node(
            "product", fact.product, source_type, source_id
        )
        city_node = await self._maybe_node("city", fact.city, source_type, source_id)

        for node in [
            customer_node,
            industry_node,
            domain_node,
            project_node,
            product_node,
            city_node,
        ]:
            if node is not None:
                created_nodes.append(node)

        relation_specs = [
            (customer_node, "in_industry", industry_node),
            (customer_node, "serves_domain", domain_node),
            (customer_node, "has_project", project_node),
            (customer_node, "uses_product", product_node),
            (customer_node, "located_in", city_node),
            (project_node, "in_industry", industry_node),
            (project_node, "serves_domain", domain_node),
            (project_node, "uses_product", product_node),
            (project_node, "located_in", city_node),
        ]

        case_node = None
        if fact.case_id:
            case_node = await self._source_node(
                "case", fact.case_id, fact.project or fact.customer or "case"
            )
            created_nodes.append(case_node)
            relation_specs.extend(
                [
                    (customer_node, "has_case", case_node),
                    (case_node, "in_industry", industry_node),
                    (case_node, "serves_domain", domain_node),
                    (case_node, "uses_product", product_node),
                    (case_node, "located_in", city_node),
                    (case_node, "references", project_node),
                ]
            )

        engagement_node = None
        if fact.engagement_id:
            engagement_node = await self._source_node(
                "project",
                fact.engagement_id,
                fact.project or fact.customer or "engagement",
                source_type="engagement",
            )
            created_nodes.append(engagement_node)
            relation_specs.extend(
                [
                    (customer_node, "has_project", engagement_node),
                    (engagement_node, "in_industry", industry_node),
                    (engagement_node, "serves_domain", domain_node),
                    (engagement_node, "uses_product", product_node),
                    (engagement_node, "located_in", city_node),
                ]
            )

        artifact_node = None
        if fact.artifact_id:
            artifact_node = await self._source_node(
                "artifact", fact.artifact_id, fact.project or fact.customer or "artifact"
            )
            created_nodes.append(artifact_node)
            relation_specs.extend(
                [
                    (customer_node, "supports_artifact", artifact_node),
                    (project_node, "supports_artifact", artifact_node),
                    (case_node, "supports_artifact", artifact_node),
                    (artifact_node, "in_industry", industry_node),
                    (artifact_node, "serves_domain", domain_node),
                    (artifact_node, "uses_product", product_node),
                    (artifact_node, "located_in", city_node),
                ]
            )

        for from_node, relation_type, to_node in relation_specs:
            if from_node is None or to_node is None:
                continue
            edge = await self.edges.upsert_edge(
                from_node_id=from_node.id,
                relation_type=relation_type,
                to_node_id=to_node.id,
                weight=1.0,
                confidence=fact.confidence,
                source_type=source_type,
                source_id=source_id,
                evidence=fact.evidence,
                properties_json={"fact": fact.model_dump(mode="json")},
            )
            created_edges.append(edge)

        return GraphFactResponse(
            nodes=[GraphNodeResponse.model_validate(node) for node in _unique_nodes(created_nodes)],
            edges=[GraphEdgeResponse.model_validate(edge) for edge in created_edges],
        )

    async def rebuild_from_sources(self) -> GraphFactResponse:
        customers = (await self.session.execute(select(Customer))).scalars().all()
        for customer in customers:
            await self.upsert_fact(
                GraphFactInput(
                    industry=customer.industry,
                    customer=customer.company or customer.name,
                    city=customer.city,
                    source_type="customer",
                    evidence=customer.notes or "",
                    confidence=0.9,
                )
            )

        cases = (await self.session.execute(select(SuccessCase))).scalars().all()
        for case in cases:
            await self.upsert_fact(
                GraphFactInput(
                    industry=case.industry,
                    customer=case.company_name,
                    domain=case.product,
                    project=case.title,
                    product=case.product,
                    city=case.city,
                    case_id=case.id,
                    source_type="case",
                    evidence=case.summary or "",
                    confidence=0.95,
                )
            )

        engagements = (await self.session.execute(select(Engagement))).scalars().all()
        for engagement in engagements:
            await self.upsert_fact(
                GraphFactInput(
                    industry=_json_value(engagement.sales_json, "industry"),
                    customer=engagement.company or engagement.name,
                    domain=_first_value(
                        _json_value(engagement.sales_json, "domain"),
                        _json_value(engagement.presales_json, "domain"),
                        _json_value(engagement.delivery_json, "domain"),
                    ),
                    project=engagement.name,
                    product=_first_value(
                        _json_value(engagement.sales_json, "product"),
                        _json_value(engagement.presales_json, "product"),
                        _json_value(engagement.delivery_json, "product"),
                    ),
                    city=_first_value(
                        _json_value(engagement.sales_json, "city"),
                        _json_value(engagement.presales_json, "city"),
                        _json_value(engagement.delivery_json, "city"),
                    ),
                    engagement_id=engagement.id,
                    source_type="engagement",
                    evidence=_first_value(
                        _json_value(engagement.sales_json, "summary"),
                        _json_value(engagement.presales_json, "summary"),
                        _json_value(engagement.delivery_json, "summary"),
                        "",
                    ),
                    confidence=0.85,
                )
            )

        artifacts = (await self.session.execute(select(BusinessArtifact))).scalars().all()
        for artifact in artifacts:
            await self.upsert_fact(
                GraphFactInput(
                    industry=_json_value(artifact.metadata_json, "industry"),
                    customer=_json_value(artifact.metadata_json, "customer"),
                    domain=_first_value(
                        _json_value(artifact.metadata_json, "domain"),
                        artifact.artifact_type,
                    ),
                    project=_json_value(artifact.metadata_json, "project"),
                    product=_json_value(artifact.metadata_json, "product"),
                    city=_json_value(artifact.metadata_json, "city"),
                    artifact_id=artifact.id,
                    source_type="artifact",
                    evidence=artifact.summary or artifact.content[:500],
                    confidence=0.8,
                )
            )

        nodes = (await self.session.execute(select(GraphNode))).scalars().all()
        edges = (await self.session.execute(select(GraphEdge))).scalars().all()

        return GraphFactResponse(
            nodes=[GraphNodeResponse.model_validate(node) for node in nodes],
            edges=[GraphEdgeResponse.model_validate(edge) for edge in edges],
        )

    async def recall(self, body: GraphRecallRequest) -> GraphRecallResponse:
        policy = self._recall_policy()
        max_hops = min(body.max_hops, policy.max_allowed_hops)
        query_nodes = await self._resolve_query_nodes(body)
        query_node_ids = [node.id for node in query_nodes]
        if not query_node_ids:
            return GraphRecallResponse(
                query_nodes=[],
                items=[],
                gate={
                    "mode": "graph",
                    "reason": "no query nodes matched",
                    "policy": _policy_metadata(policy, max_hops),
                },
            )

        touching_edges = await self.edges.edges_touching_nodes(query_node_ids)
        source_edges = await self._candidate_source_edges(
            touching_edges,
            query_node_ids,
            max_hops=max_hops,
            policy=policy,
        )
        if not source_edges:
            return GraphRecallResponse(
                query_nodes=[GraphNodeResponse.model_validate(n) for n in query_nodes],
                items=[],
                gate={
                    "mode": "graph",
                    "reason": "no connected source facts",
                    "policy": _policy_metadata(policy, max_hops),
                },
            )
        node_map = await self._node_map_for_edges(source_edges)
        source_records = await self._load_source_records(
            source_edges,
            body,
            query_node_ids=query_node_ids,
            node_map=node_map,
        )
        scored = self._score_records(
            source_records=source_records,
            query_nodes=query_nodes,
            source_edges=source_edges,
            node_map=node_map,
            body=body,
            policy=policy,
        )
        scored.sort(key=lambda item: item.score, reverse=True)
        return GraphRecallResponse(
            query_nodes=[GraphNodeResponse.model_validate(n) for n in query_nodes],
            items=scored[: body.limit],
            gate={
                "mode": "graph_first",
                "query_node_count": len(query_nodes),
                "candidate_source_count": len(source_records),
                "returned": min(len(scored), body.limit),
                "policy": _policy_metadata(policy, max_hops),
            },
        )

    async def _maybe_node(
        self,
        node_type: str,
        name: str | None,
        source_type: str,
        source_id: UUID | None,
    ) -> GraphNode | None:
        if not name or not name.strip():
            return None
        return await self.nodes.upsert_node(
            node_type=node_type,
            name=name.strip(),
            canonical_name=canonicalize(name),
            source_type=source_type,
            source_id=source_id,
        )

    async def _source_node(
        self,
        node_type: str,
        source_id: UUID,
        fallback_name: str,
        source_type: str | None = None,
    ) -> GraphNode:
        resolved_source = source_type or node_type
        name = await self._source_title(resolved_source, source_id, fallback_name)
        return await self.nodes.upsert_node(
            node_type=node_type,
            name=name,
            canonical_name=f"{resolved_source}:{source_id}",
            source_type=resolved_source,
            source_id=source_id,
        )

    async def _source_title(
        self,
        source_type: str,
        source_id: UUID,
        fallback_name: str,
    ) -> str:
        model = {
            "case": SuccessCase,
            "engagement": Engagement,
            "artifact": BusinessArtifact,
        }.get(source_type)
        if model is None:
            return fallback_name
        result = await self.session.execute(select(model).where(model.id == source_id))
        item = result.scalar_one_or_none()
        if item is None:
            return fallback_name
        return getattr(item, "title", None) or getattr(item, "name", None) or fallback_name

    async def _resolve_query_nodes(self, body: GraphRecallRequest) -> list[GraphNode]:
        specs = [
            ("industry", body.industry),
            ("customer", body.customer),
            ("domain", body.domain),
            ("project", body.project),
            ("product", body.product),
            ("city", body.city),
        ]
        nodes: list[GraphNode] = []
        for node_type, value in specs:
            if not value:
                continue
            existing = await self.nodes.find_by_identity(node_type, canonicalize(value))
            if existing is not None:
                nodes.append(existing)
        return _unique_nodes(nodes)

    def _recall_policy(self) -> GraphRecallPolicy:
        return getattr(self, "recall_policy", DEFAULT_RECALL_POLICY)

    async def _node_map_for_edges(self, edges: list[GraphEdge]) -> dict[UUID, GraphNode]:
        node_ids = {edge.from_node_id for edge in edges} | {edge.to_node_id for edge in edges}
        if not node_ids:
            return {}
        result = await self.session.execute(
            select(GraphNode).where(GraphNode.id.in_(node_ids))
        )
        return {node.id: node for node in result.scalars().all()}

    async def _candidate_source_edges(
        self,
        touching_edges: list[GraphEdge],
        query_node_ids: list[UUID],
        max_hops: int | None = None,
        policy: GraphRecallPolicy | None = None,
    ) -> list[GraphEdge]:
        active_policy = policy or self._recall_policy()
        active_max_hops = max_hops or active_policy.default_max_hops
        query_set = set(query_node_ids)
        candidate_sources: set[tuple[str, UUID]] = set()
        candidate_node_ids: set[UUID] = set()
        bridge_node_ids: set[UUID] = set()
        visited_nodes = set(query_node_ids)
        for edge in touching_edges:
            if edge.relation_type not in active_policy.allowed_recall_relations:
                continue
            if edge.from_node_id not in query_set and edge.to_node_id not in query_set:
                continue
            if edge.source_id is None:
                if edge.relation_type in active_policy.bridge_relations:
                    if edge.to_node_id in query_set:
                        candidate_node_ids.add(edge.from_node_id)
                    elif edge.from_node_id in query_set:
                        bridge_node_ids.add(edge.to_node_id)
                    continue
                other_node_id = (
                    edge.from_node_id
                    if edge.from_node_id not in query_set
                    else edge.to_node_id
                )
                candidate_node_ids.add(other_node_id)
                continue
            candidate_sources.add((edge.source_type, edge.source_id))
        candidates: list[GraphEdge] = []
        source_types = {source_type for source_type, _source_id in candidate_sources}
        source_ids = {source_id for _source_type, source_id in candidate_sources}
        if source_types and source_ids:
            result = await self.session.execute(
                select(GraphEdge).where(
                    GraphEdge.source_type.in_(source_types),
                    GraphEdge.source_id.in_(source_ids),
                )
            )
            candidates.extend(result.scalars().all())
        if candidate_node_ids:
            candidates.extend(await self.edges.edges_for_sources(list(candidate_node_ids)))
        if active_max_hops >= 2 and bridge_node_ids:
            candidates.extend(
                await self._bridge_candidate_edges(
                    bridge_node_ids=bridge_node_ids,
                    visited_nodes=visited_nodes,
                    policy=active_policy,
                )
            )
        return _unique_edges(candidates)

    async def _bridge_candidate_edges(
        self,
        *,
        bridge_node_ids: set[UUID],
        visited_nodes: set[UUID],
        policy: GraphRecallPolicy,
    ) -> list[GraphEdge]:
        candidates: list[GraphEdge] = []
        for bridge_node_id in bridge_node_ids:
            if bridge_node_id in visited_nodes:
                continue
            visited_nodes.add(bridge_node_id)
            bridge_edges = list(await self.edges.edges_touching_nodes([bridge_node_id]))
            if len(bridge_edges) > policy.max_edges_per_bridge_node:
                continue
            allowed_edges = [
                edge
                for edge in bridge_edges
                if edge.relation_type in policy.bridge_relations
                and _other_node_id(edge, bridge_node_id) not in visited_nodes
            ]
            candidates.extend(_mark_recall_hop(edge, 2) for edge in allowed_edges)
        return candidates

    async def _load_source_records(
        self,
        source_edges: list[GraphEdge],
        body: GraphRecallRequest,
        query_node_ids: list[UUID],
        node_map: dict[UUID, GraphNode],
    ) -> list[SourceRecord]:
        case_ids = _source_ids(source_edges, "case")
        engagement_ids = _source_ids(source_edges, "engagement")
        artifact_ids = _source_ids(source_edges, "artifact") if body.include_artifacts else set()
        records: list[SourceRecord] = []

        if case_ids:
            rows = (
                await self.session.execute(select(SuccessCase).where(SuccessCase.id.in_(case_ids)))
            ).scalars().all()
            records.extend(
                SourceRecord(
                    source_type="case",
                    source_id=row.id,
                    title=row.title,
                    payload=_case_payload(row),
                )
                for row in rows
            )
        if engagement_ids:
            rows = (
                await self.session.execute(select(Engagement).where(Engagement.id.in_(engagement_ids)))
            ).scalars().all()
            records.extend(
                SourceRecord(
                    source_type="engagement",
                    source_id=row.id,
                    title=row.name,
                    payload=_engagement_payload(row),
                )
                for row in rows
            )
        if artifact_ids:
            rows = (
                await self.session.execute(
                    select(BusinessArtifact).where(BusinessArtifact.id.in_(artifact_ids))
                )
            ).scalars().all()
            records.extend(
                SourceRecord(
                    source_type="artifact",
                    source_id=row.id,
                    title=row.title,
                    payload=_artifact_payload(row),
                )
                for row in rows
            )
        records.extend(_graph_node_records(source_edges, query_node_ids, node_map))
        return records

    def _score_records(
        self,
        *,
        source_records: list[SourceRecord],
        query_nodes: list[GraphNode],
        source_edges: list[GraphEdge],
        node_map: dict[UUID, GraphNode],
        body: GraphRecallRequest,
        policy: GraphRecallPolicy,
    ) -> list[GraphRecallItem]:
        edges_by_source: dict[tuple[str, UUID], list[GraphEdge]] = defaultdict(list)
        query_ids = {node.id for node in query_nodes}
        for edge in source_edges:
            if edge.relation_type not in policy.allowed_recall_relations:
                continue
            if edge.source_id:
                edges_by_source[(edge.source_type, edge.source_id)].append(edge)
                continue
            if edge.from_node_id not in query_ids:
                node = node_map.get(edge.from_node_id)
                if node and node.node_type in policy.result_node_types:
                    edges_by_source[(node.node_type, edge.from_node_id)].append(edge)
            elif edge.to_node_id not in query_ids:
                node = node_map.get(edge.to_node_id)
                if node and node.node_type in policy.result_node_types:
                    edges_by_source[(node.node_type, edge.to_node_id)].append(edge)

        scored: list[GraphRecallItem] = []
        for record in source_records:
            edges = edges_by_source[(record.source_type, record.source_id)]
            shared_ids = set()
            paths: list[GraphPathStep] = []
            for edge in edges:
                from_node = node_map.get(edge.from_node_id)
                to_node = node_map.get(edge.to_node_id)
                if from_node is None or to_node is None:
                    continue
                if edge.to_node_id in query_ids:
                    shared_ids.add(edge.to_node_id)
                    paths.append(_path_step(from_node, edge, to_node))
                elif edge.from_node_id in query_ids:
                    shared_ids.add(edge.from_node_id)
                    paths.append(_path_step(from_node, edge, to_node))
                elif _recall_hop(edge) == 2:
                    bridge_node = _bridge_node_for_edge(from_node, edge, to_node, policy)
                    if bridge_node is not None:
                        shared_ids.add(bridge_node.id)
                        paths.append(_path_step(from_node, edge, to_node))

            if not shared_ids:
                continue

            score = sum(_edge_score(edge) for edge in edges if edge.from_node_id in shared_ids or edge.to_node_id in shared_ids)
            if body.query:
                score += _lexical_bonus(body.query, record.payload)
            shared_nodes = [
                GraphNodeResponse.model_validate(node_map[node_id])
                for node_id in shared_ids
                if node_id in node_map
            ]
            scored.append(
                GraphRecallItem(
                    target_type=record.source_type,
                    target_id=record.source_id,
                    title=record.title,
                    score=round(score, 4),
                    shared_nodes=shared_nodes,
                    paths=paths[:8],
                    payload=record.payload,
                )
            )
        return scored


def canonicalize(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def graph_node_service(session: AsyncSession) -> GraphNodeService:
    return GraphNodeService(GraphNodeRepository(session))


def graph_edge_service(session: AsyncSession) -> GraphEdgeService:
    return GraphEdgeService(GraphEdgeRepository(session))


def _validate_node_type(value: str) -> None:
    if value not in GRAPH_NODE_TYPES:
        raise ValidationError(f"Unsupported graph node type: {value}", "node_type")


def _validate_relation_type(value: str) -> None:
    if value not in GRAPH_RELATION_TYPES:
        raise ValidationError(
            f"Unsupported graph relation type: {value}", "relation_type"
        )


def _source_from_fact(fact: GraphFactInput) -> tuple[str, UUID | None]:
    if fact.case_id:
        return "case", fact.case_id
    if fact.engagement_id:
        return "engagement", fact.engagement_id
    if fact.artifact_id:
        return "artifact", fact.artifact_id
    return fact.source_type, fact.source_id


def _unique_nodes(nodes: list[GraphNode]) -> list[GraphNode]:
    seen: set[UUID] = set()
    result: list[GraphNode] = []
    for node in nodes:
        if node.id in seen:
            continue
        seen.add(node.id)
        result.append(node)
    return result


def _unique_edges(edges: list[GraphEdge]) -> list[GraphEdge]:
    seen: set[UUID] = set()
    result: list[GraphEdge] = []
    for edge in edges:
        if edge.id in seen:
            continue
        seen.add(edge.id)
        result.append(edge)
    return result


def _mark_recall_hop(edge: GraphEdge, hop: int) -> GraphEdge:
    marked = copy(edge)
    properties = dict(getattr(marked, "properties_json", None) or {})
    properties["recall_hop"] = hop
    marked.properties_json = properties
    return marked


def _other_node_id(edge: GraphEdge, node_id: UUID) -> UUID:
    if edge.from_node_id == node_id:
        return edge.to_node_id
    return edge.from_node_id


def _source_ids(edges: list[GraphEdge], source_type: str) -> set[UUID]:
    return {
        edge.source_id
        for edge in edges
        if edge.source_type == source_type and edge.source_id is not None
    }


def _graph_node_records(
    edges: list[GraphEdge],
    query_node_ids: list[UUID],
    node_map: dict[UUID, GraphNode],
) -> list[SourceRecord]:
    query_ids = set(query_node_ids)
    records: dict[UUID, SourceRecord] = {}
    for edge in edges:
        if edge.source_id is not None:
            continue
        candidate_id = None
        if edge.from_node_id not in query_ids:
            candidate_id = edge.from_node_id
        elif edge.to_node_id not in query_ids:
            candidate_id = edge.to_node_id
        if candidate_id is None or candidate_id in records:
            continue
        node = node_map.get(candidate_id)
        if node is None:
            continue
        records[candidate_id] = SourceRecord(
            source_type=node.node_type,
            source_id=node.id,
            title=node.name,
            payload={
                "id": str(node.id),
                "node_type": node.node_type,
                "name": node.name,
                "description": node.description,
                "source_type": node.source_type,
                "source_id": str(node.source_id) if node.source_id else None,
                "properties_json": node.properties_json,
            },
        )
    return list(records.values())


def _path_step(from_node: GraphNode, edge: GraphEdge, to_node: GraphNode) -> GraphPathStep:
    return GraphPathStep(
        from_node=GraphNodeResponse.model_validate(from_node),
        relation_type=edge.relation_type,
        to_node=GraphNodeResponse.model_validate(to_node),
        evidence=edge.evidence,
        confidence=float(edge.confidence),
    )


def _edge_score(edge: GraphEdge) -> float:
    hop = _recall_hop(edge)
    decay = DEFAULT_RECALL_POLICY.bridge_decay ** (hop - 1)
    return float(edge.weight) * float(edge.confidence) * decay


def _recall_hop(edge: GraphEdge) -> int:
    if isinstance(edge.properties_json, dict):
        value = edge.properties_json.get("recall_hop")
        if isinstance(value, int):
            return max(value, 1)
    return 1


def _bridge_node_for_edge(
    from_node: GraphNode,
    edge: GraphEdge,
    to_node: GraphNode,
    policy: GraphRecallPolicy,
) -> GraphNode | None:
    if edge.relation_type not in policy.bridge_relations:
        return None
    if from_node.node_type not in policy.result_node_types:
        return from_node
    if to_node.node_type not in policy.result_node_types:
        return to_node
    return None


def _policy_metadata(policy: GraphRecallPolicy, max_hops: int) -> dict:
    return {
        "max_hops": max_hops,
        "max_allowed_hops": policy.max_allowed_hops,
        "bridge_decay": policy.bridge_decay,
        "max_edges_per_bridge_node": policy.max_edges_per_bridge_node,
        "allowed_recall_relations": sorted(policy.allowed_recall_relations),
        "bridge_relations": sorted(policy.bridge_relations),
        "result_node_types": sorted(policy.result_node_types),
    }


def _lexical_bonus(query: str, payload: dict) -> float:
    text = " ".join(str(value) for value in payload.values() if value is not None).lower()
    terms = [term for term in re.split(r"\s+", query.lower()) if term]
    return sum(0.25 for term in terms if term in text)


def _case_payload(row: SuccessCase) -> dict:
    return {
        "id": str(row.id),
        "title": row.title,
        "company_name": row.company_name,
        "industry": row.industry,
        "city": row.city,
        "product": row.product,
        "summary": row.summary,
        "key_points": row.key_points,
    }


def _engagement_payload(row: Engagement) -> dict:
    return {
        "id": str(row.id),
        "name": row.name,
        "company": row.company,
        "stage": row.stage,
        "status": row.status,
        "sales_json": row.sales_json,
        "presales_json": row.presales_json,
        "delivery_json": row.delivery_json,
        "next_actions": row.next_actions,
        "risks": row.risks,
    }


def _artifact_payload(row: BusinessArtifact) -> dict:
    return {
        "id": str(row.id),
        "title": row.title,
        "artifact_type": row.artifact_type,
        "summary": row.summary,
        "content": row.content,
        "source": row.source,
        "metadata_json": row.metadata_json,
        "tags": row.tags,
    }


def _json_value(value: dict | None, key: str) -> str | None:
    if not value:
        return None
    result = value.get(key)
    if isinstance(result, str):
        return result
    return None


def _first_value(*values: str | None) -> str | None:
    for value in values:
        if value:
            return value
    return None
