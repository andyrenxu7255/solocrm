from __future__ import annotations

from app.domains.visit.models import VisitPlan, VisitRecord
from app.shared.base_repository import BaseRepository


class VisitPlanRepository(BaseRepository[VisitPlan]):
    model = VisitPlan


class VisitRecordRepository(BaseRepository[VisitRecord]):
    model = VisitRecord
