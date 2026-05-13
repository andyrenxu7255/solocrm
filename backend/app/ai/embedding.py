from __future__ import annotations

from app.ai.client import AIClient

_client: AIClient | None = None


def _get_client() -> AIClient:
    global _client
    if _client is None:
        _client = AIClient()
    return _client


async def generate_embedding(text: str) -> list[float]:
    client = _get_client()
    embeddings = await client.embed([text])
    return embeddings[0]


async def generate_embeddings(texts: list[str]) -> list[list[float]]:
    client = _get_client()
    return await client.embed(texts)
