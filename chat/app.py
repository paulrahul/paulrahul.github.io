"""FastAPI application for Rahul's portfolio assistant."""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

if __package__:
    from .rag import RagService
else:
    from rag import RagService


APP_DIR = Path(__file__).resolve().parent
LOGGER = logging.getLogger(__name__)
DEFAULT_ALLOWED_ORIGINS = (
    "https://paulrahul.github.io",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
)


class ChatRequest(BaseModel):
    question: Annotated[str, Field(min_length=1, max_length=1_000)]


class SourceResponse(BaseModel):
    title: str
    url: str
    heading: str
    kind: str
    score: float
    lexicalScore: float
    retrievalScore: float


class ChatResponse(BaseModel):
    answer: str
    relevant: bool
    sources: list[SourceResponse]


def _allowed_origins() -> list[str]:
    configured = os.getenv("PORTFOLIO_ALLOWED_ORIGINS")
    if not configured:
        return list(DEFAULT_ALLOWED_ORIGINS)
    return [origin.strip() for origin in configured.split(",") if origin.strip()]


def create_app(*, service: RagService | None = None) -> FastAPI:
    load_dotenv(APP_DIR / ".env")
    data_dir = Path(os.getenv("PORTFOLIO_RAG_DATA_DIR", APP_DIR / "data"))
    answer_model = os.getenv("PORTFOLIO_CHAT_MODEL", "")
    relevance_threshold = float(
        os.getenv("PORTFOLIO_RAG_RELEVANCE_THRESHOLD", "0.3")
    )
    top_k = int(os.getenv("PORTFOLIO_RAG_TOP_K", "8"))
    if not 1 <= top_k <= 12:
        raise ValueError("PORTFOLIO_RAG_TOP_K must be between 1 and 12.")

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        active_service = service or RagService.load(
            data_dir,
            answer_model=answer_model,
            relevance_threshold=relevance_threshold,
        )
        app.state.rag_service = active_service
        try:
            yield
        finally:
            await active_service.close()

    application = FastAPI(
        title="Rahul Paul Portfolio Assistant",
        version="0.1.0",
        lifespan=lifespan,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=_allowed_origins(),
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )

    @application.get("/health")
    async def health(request: Request) -> dict[str, Any]:
        rag_service: RagService = request.app.state.rag_service
        return {
            "status": "ok",
            "chunks": rag_service.chunk_count,
            "embeddingModel": rag_service.embedding_model,
            "embeddingDimensions": rag_service.embedding_dimensions,
            "answerModel": rag_service.answer_model,
        }

    @application.post("/api/chat", response_model=ChatResponse)
    async def chat(payload: ChatRequest, request: Request) -> ChatResponse:
        try:
            result = await request.app.state.rag_service.ask(
                payload.question,
                limit=top_k,
            )
            return ChatResponse(**result.to_dict())
        except RuntimeError as error:
            LOGGER.warning("Portfolio answer generation failed: %s", error)
            raise HTTPException(
                status_code=502,
                detail="The portfolio assistant could not prepare an answer right now.",
            ) from error
        except Exception as error:
            LOGGER.exception("Portfolio chat request failed")
            raise HTTPException(
                status_code=502,
                detail="The portfolio assistant could not prepare an answer right now.",
            ) from error

    application.mount(
        "/",
        StaticFiles(directory=APP_DIR / "static", html=True),
        name="chat-ui",
    )
    return application


app = create_app()


__all__ = ["app", "create_app"]
