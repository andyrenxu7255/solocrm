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
