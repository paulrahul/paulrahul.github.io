"""OpenRouter embedding client used by the local ingestion command."""

from __future__ import annotations

import os
from collections.abc import Sequence

from dotenv import load_dotenv
from openai import OpenAI


OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_REFERER = "https://paulrahul.github.io/"
DEFAULT_TITLE = "Portfolio Assistant - Embedder"


class OpenRouterEmbeddingClient:
    def __init__(
        self,
        model: str,
        *,
        api_key: str | None = None,
        batch_size: int = 64,
        timeout: float = 60.0,
    ) -> None:
        load_dotenv()
        self.model = model.strip()
        self.batch_size = batch_size
        api_key = api_key or os.getenv("OPENROUTER_API_KEY")

        if not self.model:
            raise ValueError("An embedding model is required.")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY is required to create embeddings.")
        if batch_size < 1:
            raise ValueError("Embedding batch size must be at least one.")

        self._client = OpenAI(
            api_key=api_key,
            base_url=OPENROUTER_BASE_URL,
            default_headers={"HTTP-Referer": DEFAULT_REFERER, "X-Title": DEFAULT_TITLE},
            max_retries=2,
            timeout=timeout,
        )

    def embed_documents(self, texts: Sequence[str]) -> tuple[list[list[float]], int]:
        values = [text.strip() for text in texts]
        if not values or any(not value for value in values):
            raise ValueError("Embedding inputs must contain non-empty text.")

        vectors: list[list[float]] = []
        request_count = 0
        for start in range(0, len(values), self.batch_size):
            batch = values[start : start + self.batch_size]
            response = self._client.embeddings.create(model=self.model, input=batch)
            request_count += 1
            data = sorted(response.data, key=lambda item: item.index)
            if len(data) != len(batch):
                raise RuntimeError("OpenRouter returned an unexpected number of embeddings.")
            vectors.extend([list(item.embedding) for item in data])

        if not vectors or any(not vector for vector in vectors):
            raise RuntimeError("OpenRouter returned an empty embedding.")
        dimensions = len(vectors[0])
        if any(len(vector) != dimensions for vector in vectors):
            raise RuntimeError("OpenRouter returned embeddings with inconsistent dimensions.")
        return vectors, request_count

    def close(self) -> None:
        self._client.close()
