"""Load the generated vector index and retrieve relevant portfolio chunks."""

from __future__ import annotations

import json
import math
import os
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from dotenv import load_dotenv
from openai import AsyncOpenAI


OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_REFERER = "https://paulrahul.github.io/"
DEFAULT_TITLE = "Portfolio Assistant"
RRF_CONSTANT = 60
STOP_WORDS = {
    "a",
    "about",
    "an",
    "and",
    "are",
    "does",
    "for",
    "from",
    "has",
    "have",
    "his",
    "in",
    "is",
    "me",
    "of",
    "on",
    "rahul",
    "tell",
    "that",
    "the",
    "to",
    "what",
    "which",
    "with",
}
TOKEN_ALIASES = {
    "patents": "patent",
    "inventions": "invention",
    "degree": "qualification",
    "degrees": "qualification",
    "qualifications": "qualification",
    "study": "education",
    "studied": "education",
    "built": "build",
    "builds": "build",
    "building": "build",
    "engineers": "engineer",
    "kinds": "kind",
    "languages": "language",
    "leaders": "lead",
    "leadership": "lead",
    "leading": "lead",
    "led": "lead",
    "managed": "manage",
    "manager": "manage",
    "managers": "manage",
    "management": "manage",
    "mentored": "mentor",
    "mentoring": "mentor",
    "projects": "project",
    "roles": "role",
    "skills": "skill",
    "teams": "team",
    "technologies": "technology",
    "types": "type",
}


def _tokens(value: str) -> list[str]:
    tokens = re.findall(r"[a-z0-9]+", value.lower())
    return [
        TOKEN_ALIASES.get(token, token)
        for token in tokens
        if token not in STOP_WORDS and len(token) > 1
    ]


def _metadata_text(value: Any) -> str:
    if isinstance(value, dict):
        return " ".join(_metadata_text(item) for item in value.values())
    if isinstance(value, list):
        return " ".join(_metadata_text(item) for item in value)
    return str(value) if value is not None else ""


def preferred_kinds_for_question(question: str) -> set[str]:
    """Return broad corpus areas that should receive a ranking boost."""

    words = set(_tokens(question))
    preferred: set[str] = set()
    if words & {"build", "project", "portfolio"}:
        preferred.add("project")
    if words & {
        "career",
        "director",
        "employment",
        "hire",
        "hiring",
        "lead",
        "manage",
        "mentor",
        "role",
        "team",
    }:
        preferred.add("experience")
    if words & {"language", "skill", "stack", "technology"}:
        preferred.add("skills")
    if words & {"cv", "resume"}:
        preferred.add("resume")
    if words & {"patent", "invention"}:
        preferred.add("patent")
    if words & {"education", "degree", "qualification", "university", "college", "studied"}:
        preferred.add("education")
    return preferred


@dataclass(frozen=True)
class RetrievedChunk:
    """A single source excerpt returned by hybrid search."""

    id: str
    title: str
    url: str
    heading: str
    text: str
    kind: str
    score: float
    lexical_score: float = 0.0
    retrieval_score: float = 0.0
    metadata_matched: bool = False

    def source(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "url": self.url,
            "heading": self.heading,
            "kind": self.kind,
            "score": round(self.score, 4),
            "lexicalScore": round(self.lexical_score, 4),
            "retrievalScore": round(self.retrieval_score, 6),
        }


class RetrievalIndex:
    """An immutable in-memory semantic and lexical retrieval index."""

    def __init__(
        self,
        chunks: list[dict[str, Any]],
        embeddings: np.ndarray,
        *,
        model_name: str,
        api_key: str | None = None,
    ) -> None:
        if not chunks:
            raise ValueError("The retrieval index contains no chunks.")
        if embeddings.ndim != 2 or embeddings.shape[0] != len(chunks):
            raise ValueError("embeddings.npy does not match chunks.json.")
        if embeddings.shape[1] == 0:
            raise ValueError("The retrieval index has no vector dimensions.")

        self._chunks = chunks
        self._embeddings = self._normalise_rows(
            np.asarray(embeddings, dtype=np.float32)
        )
        self.model_name = model_name
        self._api_key = api_key
        self._client: AsyncOpenAI | None = None
        self._term_frequencies: list[Counter[str]] = []
        self._metadata_terms: list[set[str]] = []
        document_frequencies: Counter[str] = Counter()
        document_lengths: list[int] = []
        for chunk in chunks:
            heading_tokens = _tokens(str(chunk["heading"]))
            metadata_tokens = _tokens(_metadata_text(chunk.get("metadata", {})))
            kind_tokens = _tokens(str(chunk["kind"]))
            document_tokens = [
                *_tokens(str(chunk["text"])),
                *heading_tokens,
                *heading_tokens,
                *metadata_tokens,
                *metadata_tokens,
                *kind_tokens,
            ]
            frequencies = Counter(document_tokens)
            self._term_frequencies.append(frequencies)
            self._metadata_terms.append(set(heading_tokens + metadata_tokens + kind_tokens))
            document_lengths.append(len(document_tokens))
            document_frequencies.update(frequencies.keys())
        self._document_lengths = np.asarray(document_lengths, dtype=np.float32)
        self._average_document_length = float(np.mean(self._document_lengths))
        self._inverse_document_frequencies = {
            term: math.log(
                1.0
                + (len(chunks) - frequency + 0.5) / (frequency + 0.5)
            )
            for term, frequency in document_frequencies.items()
        }

    @classmethod
    def load(
        cls,
        data_dir: Path,
        *,
        api_key: str | None = None,
    ) -> "RetrievalIndex":
        """Load and validate artifacts produced by the ingestion command."""

        chunks_path = data_dir / "chunks.json"
        embeddings_path = data_dir / "embeddings.npy"
        manifest_path = data_dir / "index-manifest.json"
        for path in (chunks_path, embeddings_path, manifest_path):
            if not path.is_file():
                raise FileNotFoundError(
                    f"Missing retrieval artifact: {path}. Run the ingestion command first."
                )

        chunks_document = json.loads(chunks_path.read_text(encoding="utf-8"))
        if not isinstance(chunks_document, dict) or not isinstance(
            chunks_document.get("chunks"), list
        ):
            raise ValueError("chunks.json must contain a top-level 'chunks' list.")
        chunks = chunks_document["chunks"]
        required_fields = {
            "id",
            "sourceId",
            "sourceTitle",
            "sourceUrl",
            "heading",
            "kind",
            "text",
        }
        for number, chunk in enumerate(chunks, start=1):
            if not isinstance(chunk, dict) or not required_fields <= set(chunk):
                raise ValueError(
                    f"chunks.json entry {number} is missing required retrieval fields."
                )

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        embedding = manifest.get("embedding") if isinstance(manifest, dict) else None
        if not isinstance(embedding, dict) or embedding.get("status") != "created":
            raise ValueError(
                "The index manifest has no created embeddings. Run ingestion without "
                "--skip-embeddings."
            )
        model_name = embedding.get("model")
        if not isinstance(model_name, str) or not model_name.strip():
            raise ValueError("The index manifest does not record an embedding model.")
        if manifest.get("chunkCount") != len(chunks):
            raise ValueError("The manifest chunk count does not match chunks.json.")
        recorded_source_counts = manifest.get("chunkCountsBySource")
        if recorded_source_counts is not None:
            actual_source_counts = Counter(str(chunk["sourceId"]) for chunk in chunks)
            if not isinstance(recorded_source_counts, dict) or {
                str(source_id): int(count)
                for source_id, count in recorded_source_counts.items()
            } != dict(actual_source_counts):
                raise ValueError(
                    "The manifest source chunk counts do not match chunks.json."
                )

        embeddings = np.load(embeddings_path, allow_pickle=False)
        index = cls(chunks, embeddings, model_name=model_name, api_key=api_key)
        dimensions = embedding.get("dimensions")
        if dimensions is not None and dimensions != index.dimensions:
            raise ValueError(
                "The manifest dimensions do not match embeddings.npy."
            )
        return index

    @property
    def dimensions(self) -> int:
        return int(self._embeddings.shape[1])

    @property
    def chunk_count(self) -> int:
        return len(self._chunks)

    def kind_count(self, kind: str) -> int:
        return sum(1 for chunk in self._chunks if str(chunk["kind"]) == kind)

    def overview_chunks(self) -> list[RetrievedChunk]:
        """Return the complete profile for context, independent of search ranking."""
        return [
            RetrievedChunk(
                id=str(chunk["id"]),
                title=str(chunk["sourceTitle"]),
                url=str(chunk["sourceUrl"]),
                heading=str(chunk["heading"]),
                text=str(chunk["text"]),
                kind="overview",
                # Included unconditionally, not assigned a synthetic similarity.
                score=0.0,
            )
            for chunk in self._chunks
            if chunk["kind"] == "overview"
        ]

    def _lexical_scores(self, question: str) -> tuple[np.ndarray, list[set[str]]]:
        query_terms = set(_tokens(question))
        scores = np.zeros(self.chunk_count, dtype=np.float32)
        matched_terms: list[set[str]] = [set() for _ in self._chunks]
        if not query_terms:
            return scores, matched_terms

        k1 = 1.5
        length_weight = 0.75
        for index, frequencies in enumerate(self._term_frequencies):
            document_length = float(self._document_lengths[index])
            normalizer = k1 * (
                1.0
                - length_weight
                + length_weight * document_length / self._average_document_length
            )
            for term in query_terms:
                frequency = frequencies.get(term, 0)
                if not frequency:
                    continue
                matched_terms[index].add(term)
                inverse_frequency = self._inverse_document_frequencies.get(term, 0.0)
                scores[index] += inverse_frequency * (
                    frequency * (k1 + 1.0) / (frequency + normalizer)
                )
        maximum = float(np.max(scores)) if len(scores) else 0.0
        if maximum > 0:
            scores /= maximum
        return scores, matched_terms

    @staticmethod
    def _normalise_rows(vectors: np.ndarray) -> np.ndarray:
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        if np.any(norms == 0):
            raise ValueError("The retrieval index contains a zero-length embedding.")
        return vectors / norms

    def _get_client(self) -> AsyncOpenAI:
        if self._client is None:
            load_dotenv(Path(__file__).resolve().parents[1] / ".env")
            api_key = self._api_key or os.getenv("OPENROUTER_API_KEY")
            if not api_key:
                raise ValueError("OPENROUTER_API_KEY is required to search the index.")
            self._client = AsyncOpenAI(
                api_key=api_key,
                base_url=OPENROUTER_BASE_URL,
                default_headers={
                    "HTTP-Referer": DEFAULT_REFERER,
                    "X-Title": DEFAULT_TITLE,
                },
                max_retries=2,
                timeout=30.0,
            )
        return self._client

    async def _embed_query(self, question: str) -> np.ndarray:
        response = await self._get_client().embeddings.create(
            model=self.model_name,
            input=[question],
        )
        if len(response.data) != 1 or not response.data[0].embedding:
            raise RuntimeError("OpenRouter returned an empty query embedding.")
        vector = np.asarray(response.data[0].embedding, dtype=np.float32)
        if vector.shape != (self.dimensions,):
            raise ValueError(
                f"Query embedding shape {vector.shape} does not match index "
                f"dimensions {self.dimensions}."
            )
        return self._normalise_rows(vector.reshape(1, -1))[0]

    async def search(
        self,
        question: str,
        *,
        limit: int = 8,
        preferred_kinds: set[str] | None = None,
    ) -> list[RetrievedChunk]:
        question = question.strip()
        if not question:
            raise ValueError("A question is required.")
        if limit < 1:
            raise ValueError("The retrieval limit must be at least one.")

        query_vector = await self._embed_query(question)
        semantic_scores = np.clip(self._embeddings @ query_vector, -1.0, 1.0)
        lexical_scores, matched_terms = self._lexical_scores(question)
        query_terms = set(_tokens(question))
        query_term_count = max(1, len(query_terms))
        metadata_coverage = np.asarray(
            [
                len(query_terms & metadata_terms) / query_term_count
                for metadata_terms in self._metadata_terms
            ],
            dtype=np.float32,
        )
        candidates = np.arange(self.chunk_count, dtype=int)

        semantic_order = candidates[
            np.argsort(-semantic_scores[candidates], kind="stable")
        ]
        semantic_ranks = np.empty(self.chunk_count, dtype=np.int32)
        semantic_ranks[semantic_order] = np.arange(1, self.chunk_count + 1)

        lexical_order = candidates[
            np.argsort(-lexical_scores[candidates], kind="stable")
        ]
        lexical_ranks = np.empty(self.chunk_count, dtype=np.int32)
        lexical_ranks[lexical_order] = np.arange(1, self.chunk_count + 1)

        retrieval_scores = np.asarray(
            [
                1.0 / (RRF_CONSTANT + semantic_ranks[index])
                + (
                    1.75 / (RRF_CONSTANT + lexical_ranks[index])
                    if lexical_scores[index] > 0
                    else 0.0
                )
                + (
                    0.75 / (RRF_CONSTANT + 1)
                    if preferred_kinds
                    and str(self._chunks[index]["kind"]) in preferred_kinds
                    else 0.0
                )
                + 0.75 * metadata_coverage[index] / (RRF_CONSTANT + 1)
                for index in candidates
            ],
            dtype=np.float32,
        )
        fused_order = candidates[
            np.argsort(-retrieval_scores[candidates], kind="stable")
        ]
        ranked_list: list[int] = []
        section_counts: Counter[tuple[str, str]] = Counter()
        deferred: list[int] = []
        for raw_index in fused_order:
            index = int(raw_index)
            section_key = (
                str(self._chunks[index]["sourceId"]),
                str(self._chunks[index]["heading"]),
            )
            if section_counts[section_key] >= 2:
                deferred.append(index)
                continue
            ranked_list.append(index)
            section_counts[section_key] += 1
            if len(ranked_list) == min(limit, self.chunk_count):
                break
        if len(ranked_list) < min(limit, self.chunk_count):
            for index in deferred:
                ranked_list.append(index)
                if len(ranked_list) == min(limit, self.chunk_count):
                    break
        ranked = np.asarray(ranked_list, dtype=int)

        return [
            RetrievedChunk(
                id=str(self._chunks[index]["id"]),
                title=str(
                    self._chunks[index].get("metadata", {}).get("title")
                    or self._chunks[index]["sourceTitle"]
                ),
                url=str(self._chunks[index]["sourceUrl"]),
                heading=str(self._chunks[index]["heading"]),
                text=str(self._chunks[index]["text"]),
                kind=str(self._chunks[index]["kind"]),
                score=float(semantic_scores[index]),
                lexical_score=float(lexical_scores[index]),
                retrieval_score=float(retrieval_scores[index]),
                metadata_matched=(
                    metadata_coverage[index] > 0
                    or lexical_scores[index] >= 0.5
                    or len(matched_terms[index]) / query_term_count >= 0.5
                ),
            )
            for index in ranked
        ]

    async def close(self) -> None:
        if self._client is not None:
            await self._client.close()
