from __future__ import annotations

from app.domains.case.models import SuccessCase
from app.shared.base_repository import BaseRepository


class CaseRepository(BaseRepository[SuccessCase]):
    model = SuccessCase
