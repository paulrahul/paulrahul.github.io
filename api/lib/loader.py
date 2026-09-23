"""Read-only accessors for the portfolio's data.json.

Vendored into both api/lib and mcp/lib because Vercel only bundles files inside
each service's Root Directory. Keep the two copies identical.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any
from urllib.request import urlopen

# Used when no local data.json is found, e.g. on Vercel, where the repo-root file
# lies outside the deployed bundle.
DATA_URL = "https://paulrahul.github.io/data.json"


def _local_data_path() -> Path | None:
    for directory in Path(__file__).resolve().parents:
        candidate = directory / "data.json"
        if candidate.is_file():
            return candidate
    return None


@lru_cache(maxsize=1)
def _load() -> dict[str, Any]:
    local_path = _local_data_path()
    if local_path is not None:
        return json.loads(local_path.read_text(encoding="utf-8"))
    with urlopen(DATA_URL, timeout=10) as response:
        return json.load(response)


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
