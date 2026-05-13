from __future__ import annotations

from app.ai.embedding import generate_embedding
from app.domains.customer.models import Customer
from app.domains.customer.schemas import CustomerCreate, CustomerUpdate
from app.shared.base_service import BaseService


class CustomerService(BaseService[Customer]):
    async def create_from_schema(self, data: CustomerCreate) -> Customer:
        instance = Customer(**data.model_dump())

        text = _customer_to_text(data)
        if text:
            instance.embedding = await generate_embedding(text)

        return await self.repository.create(instance)

    async def update_from_schema(
        self, instance: Customer, data: CustomerUpdate
    ) -> Customer:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(instance, field, value)

        text = _customer_instance_to_text(instance)
        if text:
            instance.embedding = await generate_embedding(text)

        return await self.repository.update(instance)


def _customer_to_text(data: CustomerCreate) -> str:
    parts = [
        data.name,
        data.company,
        data.industry,
        data.city,
        data.notes,
    ]
    return " ".join(p for p in parts if p)


def _customer_instance_to_text(instance: Customer) -> str:
    parts = [
        instance.name,
        instance.company,
        instance.industry,
        instance.city,
        instance.notes or "",
    ]
    return " ".join(p for p in parts if p)
