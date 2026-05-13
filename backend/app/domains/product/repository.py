from __future__ import annotations

from app.domains.product.models import UserProductConfig
from app.shared.base_repository import BaseRepository


class ProductConfigRepository(BaseRepository[UserProductConfig]):
    model = UserProductConfig
