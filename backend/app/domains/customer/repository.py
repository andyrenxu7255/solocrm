from __future__ import annotations

from app.domains.customer.models import Customer
from app.shared.base_repository import BaseRepository


class CustomerRepository(BaseRepository[Customer]):
    model = Customer
