"""FastAPI application exposing Rahul's portfolio data (data.json) as a small REST API."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

def _find_repo_root(start: Path) -> Path:
    """Locate the directory containing lib/, searching upward from `start`.

    Not always one fixed number of parents away: locally app.py sits nested
    inside api/, so lib/ is one level up. Deployed on Vercel, the Root
    Directory's contents are flattened to the function bundle's root, so
    app.py's own directory *is* the bundle root and lib/ (if included) may
    sit right alongside it instead of one level up.
    """
    for candidate in (start, *start.parents):
        if (candidate / "lib" / "loader.py").is_file():
            return candidate
    raise RuntimeError(f"Could not locate the 'lib' package searching upward from {start}")


APP_DIR = Path(__file__).resolve().parent
REPO_ROOT = _find_repo_root(APP_DIR)
# Appended (not inserted at index 0) so site-packages resolve first; avoids this
# directory ever shadowing a same-named third-party package.
if str(REPO_ROOT) not in sys.path:
    sys.path.append(str(REPO_ROOT))

from lib import loader  # noqa: E402

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
