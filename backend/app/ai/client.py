from __future__ import annotations

from openai import AsyncOpenAI

from app.config import get_settings
from app.shared.exceptions import ExternalServiceError


class AIClient:
    def __init__(self) -> None:
        settings = get_settings()
        self._client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_api_base,
        )
        self._llm_model = settings.llm_model
        self._embedding_model = settings.embedding_model

    @property
    def llm_model(self) -> str:
        return self._llm_model

    @property
    def embedding_model(self) -> str:
        return self._embedding_model

    async def chat(
        self,
        messages: list[dict],
        temperature: float = 0.3,
        max_tokens: int = 2048,
    ) -> str:
        try:
            response = await self._client.chat.completions.create(
                model=self._llm_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            raise ExternalServiceError("LLM", str(e)) from e

    async def embed(self, texts: list[str]) -> list[list[float]]:
        try:
            response = await self._client.embeddings.create(
                model=self._embedding_model,
                input=texts,
            )
            return [d.embedding for d in response.data]
        except Exception as e:
            raise ExternalServiceError("Embedding", str(e)) from e
