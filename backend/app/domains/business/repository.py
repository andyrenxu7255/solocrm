from __future__ import annotations

from typing import Sequence

from sqlalchemy import func, select

from app.domains.business.models import AgentActionLog, BusinessArtifact, Engagement
from app.shared.base_repository import BaseRepository
from app.shared.schemas import PaginationParams


class EngagementRepository(BaseRepository[Engagement]):
    model = Engagement

    async def get_filtered(
        self,
        pagination: PaginationParams,
        stage: str | None = None,
        status: str | None = None,
    ) -> tuple[Sequence[Engagement], int]:
        items, total = await self.get_all(pagination)
        if not stage and not status:
            return items, total

        count_q = select(func.count()).select_from(Engagement)
        q = select(Engagement)
        if stage:
            count_q = count_q.where(Engagement.stage == stage)
            q = q.where(Engagement.stage == stage)
        if status:
            count_q = count_q.where(Engagement.status == status)
            q = q.where(Engagement.status == status)
        total = (await self.session.execute(count_q)).scalar_one()
        q = q.order_by(Engagement.updated_at.desc()).offset(
            (pagination.page - 1) * pagination.page_size
        ).limit(pagination.page_size)

        result = await self.session.execute(q)
        filtered = result.scalars().all()
        return filtered, total


class ArtifactRepository(BaseRepository[BusinessArtifact]):
    model = BusinessArtifact


class AgentActionLogRepository(BaseRepository[AgentActionLog]):
    model = AgentActionLog

    async def get_filtered(
        self,
        pagination: PaginationParams,
        agent_name: str | None = None,
        action: str | None = None,
        status: str | None = None,
        target_type: str | None = None,
    ) -> tuple[Sequence[AgentActionLog], int]:
        count_q = select(func.count()).select_from(AgentActionLog)
        q = select(AgentActionLog)

        if agent_name:
            count_q = count_q.where(AgentActionLog.agent_name == agent_name)
            q = q.where(AgentActionLog.agent_name == agent_name)
        if action:
            count_q = count_q.where(AgentActionLog.action == action)
            q = q.where(AgentActionLog.action == action)
        if status:
            count_q = count_q.where(AgentActionLog.status == status)
            q = q.where(AgentActionLog.status == status)
        if target_type:
            count_q = count_q.where(AgentActionLog.target_type == target_type)
            q = q.where(AgentActionLog.target_type == target_type)

        total = (await self.session.execute(count_q)).scalar_one()
        q = q.order_by(AgentActionLog.created_at.desc()).offset(
            (pagination.page - 1) * pagination.page_size
        ).limit(pagination.page_size)

        result = await self.session.execute(q)
        return result.scalars().all(), total

    async def get_summary(self) -> dict:
        status_rows = await self.session.execute(
            select(AgentActionLog.status, func.count())
            .group_by(AgentActionLog.status)
            .order_by(AgentActionLog.status)
        )
        action_rows = await self.session.execute(
            select(AgentActionLog.action, func.count())
            .group_by(AgentActionLog.action)
            .order_by(func.count().desc(), AgentActionLog.action)
        )
        agent_rows = await self.session.execute(
            select(AgentActionLog.agent_name, func.count())
            .group_by(AgentActionLog.agent_name)
            .order_by(func.count().desc(), AgentActionLog.agent_name)
        )
        latest_errors = await self.session.execute(
            select(AgentActionLog)
            .where(AgentActionLog.status == "error")
            .order_by(AgentActionLog.created_at.desc())
            .limit(5)
        )

        return {
            "status_counts": {
                status: count for status, count in status_rows.all()
            },
            "action_counts": {
                action: count for action, count in action_rows.all()
            },
            "agent_counts": {
                agent_name: count for agent_name, count in agent_rows.all()
            },
            "latest_errors": latest_errors.scalars().all(),
        }
