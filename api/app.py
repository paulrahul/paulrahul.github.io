"""FastAPI application exposing Rahul's portfolio data (data.json) as a small REST API."""

from __future__ import annotations

import os
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from lib import loader

DEFAULT_ALLOWED_ORIGINS = (
    "https://paulrahul.github.io",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
)


def _allowed_origins() -> list[str]:
    configured = os.getenv("PORTFOLIO_ALLOWED_ORIGINS")
    if not configured:
        return list(DEFAULT_ALLOWED_ORIGINS)
    return [origin.strip() for origin in configured.split(",") if origin.strip()]


def create_app() -> FastAPI:
    application = FastAPI(
        title="Rahul Paul Portfolio API",
        version="0.1.0",
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=_allowed_origins(),
        allow_credentials=False,
        allow_methods=["GET"],
        allow_headers=["Content-Type"],
    )

    @application.get("/health")
    async def health() -> dict[str, Any]:
        return {"status": "ok"}

    @application.get("/overview")
    async def overview() -> dict[str, Any]:
        return loader.get_overview()

    @application.get("/projects")
    async def projects() -> list[dict[str, Any]]:
        return loader.get_projects()

    @application.get("/skills")
    async def skills() -> dict[str, Any]:
        return loader.get_skills()

    @application.get("/experience")
    async def experience() -> list[dict[str, Any]]:
        return loader.get_experience()

    @application.get("/education")
    async def education() -> list[dict[str, Any]]:
        return loader.get_education()

    @application.get("/patents")
    async def patents() -> dict[str, Any]:
        return loader.get_patents()

    return application


app = create_app()


__all__ = ["app", "create_app"]
