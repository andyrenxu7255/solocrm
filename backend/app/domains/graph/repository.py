from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.graph.models import GraphEdge, GraphNode
from app.shared.base_repository import BaseRepository
from app.shared.schemas import PaginationParams


class GraphNodeRepository(BaseRepository[GraphNode]):
    model = GraphNode

    async def upsert_node(
        self,
        *,
        node_type: str,
        name: str,
        canonical_name: str,
        description: str = "",
        source_type: str = "",
        source_id: UUID | None = None,
        properties_json: dict | None = None,
    ) -> GraphNode:
        values = {
            "node_type": node_type,
            "name": name,
            "canonical_name": canonical_name,
            "description": description,
            "source_type": source_type,
            "source_id": source_id,
            "properties_json": properties_json,
        }
        stmt = (
            insert(GraphNode)
            .values(**values)
            .on_conflict_do_update(
                constraint="uq_graph_node_identity",
                set_={
                    "name": name,
                    "description": description,
                    "source_type": source_type,
                    "source_id": source_id,
                    "properties_json": properties_json,
                },
            )
            .returning(GraphNode)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def find_by_identity(
        self,
        node_type: str,
        canonical_name: str,
    ) -> GraphNode | None:
        result = await self.session.execute(
            select(GraphNode).where(
                GraphNode.node_type == node_type,
                GraphNode.canonical_name == canonical_name,
            )
        )
        return result.scalar_one_or_none()

    async def list_filtered(
        self,
        pagination: PaginationParams,
        node_type: str | None = None,
        q: str | None = None,
    ) -> tuple[Sequence[GraphNode], int]:
        count_q = select(func.count()).select_from(GraphNode)
        stmt = select(GraphNode)
        if node_type:
            count_q = count_q.where(GraphNode.node_type == node_type)
            stmt = stmt.where(GraphNode.node_type == node_type)
        if q:
            pattern = f"%{q.strip().lower()}%"
            count_q = count_q.where(
                or_(
                    func.lower(GraphNode.name).like(pattern),
                    GraphNode.canonical_name.like(pattern),
                )
            )
            stmt = stmt.where(
                or_(
                    func.lower(GraphNode.name).like(pattern),
                    GraphNode.canonical_name.like(pattern),
                )
            )
        total = (await self.session.execute(count_q)).scalar_one()
        stmt = (
            stmt.order_by(GraphNode.updated_at.desc())
            .offset((pagination.page - 1) * pagination.page_size)
            .limit(pagination.page_size)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all(), total

    async def get_by_source(
        self,
        source_type: str,
        source_id: UUID,
    ) -> Sequence[GraphNode]:
        result = await self.session.execute(
            select(GraphNode).where(
                GraphNode.source_type == source_type,
                GraphNode.source_id == source_id,
            )
        )
        return result.scalars().all()


class GraphEdgeRepository(BaseRepository[GraphEdge]):
    model = GraphEdge

    async def upsert_edge(
        self,
        *,
        from_node_id: UUID,
        relation_type: str,
        to_node_id: UUID,
        weight: float = 1.0,
        confidence: float = 1.0,
        source_type: str = "",
        source_id: UUID | None = None,
        evidence: str = "",
        properties_json: dict | None = None,
    ) -> GraphEdge:
        values = {
            "from_node_id": from_node_id,
            "relation_type": relation_type,
            "to_node_id": to_node_id,
            "weight": weight,
            "confidence": confidence,
            "source_type": source_type,
            "source_id": source_id,
            "evidence": evidence,
            "properties_json": properties_json,
        }
        stmt = (
            insert(GraphEdge)
            .values(**values)
            .on_conflict_do_update(
                constraint="uq_graph_edge_fact",
                set_={
                    "weight": weight,
                    "confidence": confidence,
                    "evidence": evidence,
                    "properties_json": properties_json,
                },
            )
            .returning(GraphEdge)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def list_filtered(
        self,
        pagination: PaginationParams,
        relation_type: str | None = None,
        node_id: UUID | None = None,
    ) -> tuple[Sequence[GraphEdge], int]:
        count_q = select(func.count()).select_from(GraphEdge)
        stmt = select(GraphEdge)
        if relation_type:
            count_q = count_q.where(GraphEdge.relation_type == relation_type)
            stmt = stmt.where(GraphEdge.relation_type == relation_type)
        if node_id:
            condition = or_(
                GraphEdge.from_node_id == node_id,
                GraphEdge.to_node_id == node_id,
            )
            count_q = count_q.where(condition)
            stmt = stmt.where(condition)
        total = (await self.session.execute(count_q)).scalar_one()
        stmt = (
            stmt.order_by(GraphEdge.updated_at.desc())
            .offset((pagination.page - 1) * pagination.page_size)
            .limit(pagination.page_size)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all(), total

    async def edges_for_sources(
        self,
        source_ids: Sequence[UUID],
    ) -> Sequence[GraphEdge]:
        if not source_ids:
            return []
        result = await self.session.execute(
            select(GraphEdge).where(
                or_(
                    GraphEdge.from_node_id.in_(source_ids),
                    GraphEdge.to_node_id.in_(source_ids),
                )
            )
        )
        return result.scalars().all()

    async def edges_touching_nodes(
        self,
        node_ids: Sequence[UUID],
    ) -> Sequence[GraphEdge]:
        if not node_ids:
            return []
        result = await self.session.execute(
            select(GraphEdge).where(
                or_(
                    GraphEdge.from_node_id.in_(node_ids),
                    GraphEdge.to_node_id.in_(node_ids),
                )
            )
        )
        return result.scalars().all()
