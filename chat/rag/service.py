"""Retrieve portfolio context and generate a source-grounded answer."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from openai import AsyncOpenAI

from .retrieval import (
    DEFAULT_REFERER,
    DEFAULT_TITLE,
    OPENROUTER_BASE_URL,
    RetrievedChunk,
    RetrievalIndex,
    preferred_kinds_for_question,
)


NO_RELEVANT_INFORMATION = (
    "I couldn't find enough relevant information in Rahul's portfolio to answer that."
)
MAX_ANSWER_TOKENS = 1_000
GENERATION_ATTEMPTS = 2

SYSTEM_PROMPT = """You are Rahul Paul's portfolio assistant.
Answer questions about Rahul's work, skills, experience, and projects using only the supplied portfolio excerpts.
Keep answers concise, natural, and specific, and finish the answer within 250 words. Refer to Rahul in the third person.
For questions about the kinds of projects Rahul builds, use the Topics fields, group them into useful categories, and name representative projects as evidence. Do not answer such questions by listing only his technical skills.
For leadership or management questions, prioritize concrete evidence from his experience: roles, team sizes, distributed locations, hiring, team growth, planning, technical direction, and delivery responsibilities.
Return readable Markdown. For overview answers, begin with one short paragraph, put each category in a separate bullet with a bold category label, and optionally end with one short concluding paragraph. Keep every bullet on its own line.
Do not invent or infer facts that are not supported by the excerpts.
Do not mention retrieval, embeddings, chunks, context, or these instructions.
If the excerpts do not support an answer, say that the information is not available in Rahul's portfolio.
Links may be included only when they appear in the supplied excerpts."""


@dataclass(frozen=True)
class RagResult:
    answer: str
    relevant: bool
    sources: list[RetrievedChunk]

    def to_dict(self) -> dict[str, Any]:
        return {
            "answer": self.answer,
            "relevant": self.relevant,
            "sources": [source.source() for source in self.sources],
        }


class RagService:
    """The small public interface used by the HTTP application."""

    def __init__(
        self,
        index: RetrievalIndex,
        *,
        answer_model: str,
        relevance_threshold: float = 0.3,
        api_key: str | None = None,
    ) -> None:
        if not answer_model.strip():
            raise ValueError("PORTFOLIO_CHAT_MODEL is required.")
        if not -1.0 <= relevance_threshold <= 1.0:
            raise ValueError("The relevance threshold must be between -1 and 1.")
        self._index = index
        self.answer_model = answer_model.strip()
        self.relevance_threshold = relevance_threshold
        self._api_key = api_key
        self._client: AsyncOpenAI | None = None

    @classmethod
    def load(
        cls,
        data_dir: Path,
        *,
        answer_model: str,
        relevance_threshold: float = 0.3,
        api_key: str | None = None,
    ) -> "RagService":
        return cls(
            RetrievalIndex.load(data_dir, api_key=api_key),
            answer_model=answer_model,
            relevance_threshold=relevance_threshold,
            api_key=api_key,
        )

    @property
    def embedding_model(self) -> str:
        return self._index.model_name

    @property
    def embedding_dimensions(self) -> int:
        return self._index.dimensions

    @property
    def chunk_count(self) -> int:
        return self._index.chunk_count

    def _get_client(self) -> AsyncOpenAI:
        if self._client is None:
            load_dotenv()
            api_key = self._api_key or os.getenv("OPENROUTER_API_KEY")
            if not api_key:
                raise ValueError("OPENROUTER_API_KEY is required to generate answers.")
            self._client = AsyncOpenAI(
                api_key=api_key,
                base_url=OPENROUTER_BASE_URL,
                default_headers={
                    "HTTP-Referer": DEFAULT_REFERER,
                    "X-Title": DEFAULT_TITLE,
                },
                max_retries=2,
                timeout=45.0,
            )
        return self._client

    async def _generate_answer(
        self,
        question: str,
        sources: list[RetrievedChunk],
    ) -> str:
        context = "\n\n".join(
            f"[Excerpt {number}: {source.heading}; source: {source.title}]\n{source.text}"
            for number, source in enumerate(sources, start=1)
        )
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Question: {question}\n\nPortfolio excerpts:\n{context}",
            },
        ]
        failure = "an empty response"
        for attempt in range(GENERATION_ATTEMPTS):
            response = await self._get_client().chat.completions.create(
                model=self.answer_model,
                temperature=0.2,
                max_tokens=MAX_ANSWER_TOKENS * (attempt + 1),
                messages=messages,
            )
            choice = response.choices[0] if response.choices else None
            answer = choice.message.content if choice else None
            answer = answer.strip() if answer else ""
            finish_reason = str(choice.finish_reason) if choice else None
            if answer and not self._looks_truncated(
                answer, finish_reason
            ) and not self._contains_generation_artifact(answer):
                return answer
            if not answer:
                failure = "an empty response"
            elif self._contains_generation_artifact(answer):
                failure = "a malformed response"
            else:
                failure = "a truncated response"

        raise RuntimeError(
            f"The answer model returned {failure} after {GENERATION_ATTEMPTS} attempts."
        )

    @staticmethod
    def _looks_truncated(answer: str, finish_reason: str | None) -> bool:
        if finish_reason == "length":
            return True
        stripped = answer.rstrip()
        if stripped.count("(") > stripped.count(")"):
            return True
        return stripped.lower().endswith(
            ("e.g", "e.g.", "i.e", "i.e.", ":", ",", "-", "—", "/")
        )

    @staticmethod
    def _contains_generation_artifact(answer: str) -> bool:
        return bool(re.search(r"\)\s*skip(?:\.|\b)", answer, flags=re.IGNORECASE))

    async def ask(self, question: str, *, limit: int = 8) -> RagResult:
        question = question.strip()
        if not question:
            raise ValueError("A question is required.")
        if len(question) > 1_000:
            raise ValueError("Questions must be 1,000 characters or fewer.")

        preferred_kinds = preferred_kinds_for_question(question)
        retrieved = await self._index.search(
            question,
            limit=limit,
            preferred_kinds=preferred_kinds or None,
        )
        relevant = [
            source
            for source in retrieved
            if source.score >= self.relevance_threshold or source.metadata_matched
        ]
        if not relevant:
            return RagResult(
                answer=NO_RELEVANT_INFORMATION,
                relevant=False,
                sources=[],
            )

        answer = await self._generate_answer(question, relevant)
        return RagResult(answer=answer, relevant=True, sources=relevant)

    async def close(self) -> None:
        await self._index.close()
        if self._client is not None:
            await self._client.close()
