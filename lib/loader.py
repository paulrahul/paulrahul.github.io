"""Read-only accessors for the portfolio's data.json.

Shared by api/ (HTTP) and mcp/ (MCP tools) so both interfaces read
from the same source of truth without duplicating parsing logic.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = REPO_ROOT / "data.json"


@lru_cache(maxsize=1)
def _load() -> dict[str, Any]:
    with DATA_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def get_overview() -> dict[str, Any]:
    return _load()["overview"]


def get_projects() -> list[dict[str, Any]]:
    return _load()["projects"]


def get_skills() -> dict[str, Any]:
    return _load()["skills"]


def get_experience() -> list[dict[str, Any]]:
    return _load()["experience"]


def get_education() -> list[dict[str, Any]]:
    return _load()["education"]


def get_patents() -> dict[str, Any]:
    return _load()["patents"]


def get_all() -> dict[str, Any]:
    return _load()
