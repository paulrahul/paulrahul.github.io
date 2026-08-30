"""Load configured portfolio sources without applying RAG-specific chunking."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pdfplumber


@dataclass(frozen=True)
class SourceSpec:
    id: str
    type: str
    path: Path
    relative_path: str
    title: str
    url: str
    options: dict[str, Any]


@dataclass(frozen=True)
class LoadedSource:
    spec: SourceSpec
    sha256: str
    content: Any


def load_source_specs(config_path: Path, repository_root: Path) -> list[SourceSpec]:
    try:
        document = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"Could not read source configuration: {config_path}") from error

    entries = document.get("sources") if isinstance(document, dict) else None
    if not isinstance(entries, list) or not entries:
        raise ValueError("sources.json must contain a non-empty 'sources' array.")

    repository_root = repository_root.resolve()
    specs: list[SourceSpec] = []
    seen_ids: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError("Every configured source must be an object.")
        required = ("id", "type", "path", "title", "url")
        missing = [key for key in required if not isinstance(entry.get(key), str) or not entry[key].strip()]
        if missing:
            raise ValueError(f"A configured source is missing fields: {', '.join(missing)}")

        source_id = entry["id"].strip()
        if source_id in seen_ids:
            raise ValueError(f"Duplicate source id: {source_id}")
        seen_ids.add(source_id)

        relative_path = entry["path"].strip()
        path = (repository_root / relative_path).resolve()
        try:
            path.relative_to(repository_root)
        except ValueError as error:
            raise ValueError(f"Source path must remain inside the repository: {relative_path}") from error
        if not path.is_file():
            raise FileNotFoundError(f"Configured source does not exist: {path}")

        specs.append(
            SourceSpec(
                id=source_id,
                type=entry["type"].strip(),
                path=path,
                relative_path=relative_path,
                title=entry["title"].strip(),
                url=entry["url"].strip(),
                options=entry.get("options") if isinstance(entry.get("options"), dict) else {},
            )
        )
    return specs


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _clean_pdf_text(value: str) -> str:
    lines = [re.sub(r"\s+", " ", line).strip() for line in value.splitlines()]
    return "\n".join(line for line in lines if line)


def _trim_to_marker(text: str, marker: str | None) -> str:
    if not marker:
        return text
    match = re.search(re.escape(marker), text, flags=re.IGNORECASE)
    if not match:
        raise ValueError(f"Could not find configured PDF start marker: {marker}")
    return text[match.start() :]


def _extract_pdf(spec: SourceSpec) -> dict[str, Any]:
    two_column_pages = {int(page) for page in spec.options.get("twoColumnPages", [])}
    split_ratio = float(spec.options.get("columnSplitRatio", 0.65))
    if not 0.4 <= split_ratio <= 0.8:
        raise ValueError("PDF columnSplitRatio must be between 0.4 and 0.8.")

    start_markers = spec.options.get("startMarkers", {})
    labels = spec.options.get("sectionLabels", {})
    if not isinstance(start_markers, dict) or not isinstance(labels, dict):
        raise ValueError("PDF startMarkers and sectionLabels must be objects.")

    sections: list[dict[str, Any]] = []
    with pdfplumber.open(spec.path) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            regions: list[tuple[str, Any]]
            if page_number in two_column_pages:
                split = page.width * split_ratio
                regions = [
                    ("left", page.crop((0, 0, split, page.height))),
                    ("right", page.crop((split, 0, page.width, page.height))),
                ]
            else:
                regions = [("full", page)]

            for region_name, region in regions:
                key = f"{page_number}:{region_name}"
                extracted = region.extract_text(x_tolerance=2, y_tolerance=3) or ""
                text = _clean_pdf_text(extracted)
                text = _trim_to_marker(text, start_markers.get(key))
                if not text:
                    continue
                sections.append(
                    {
                        "key": key,
                        "page": page_number,
                        "region": region_name,
                        "heading": str(labels.get(key) or f"Page {page_number}"),
                        "text": text,
                    }
                )

    if not sections:
        raise ValueError(f"No text could be extracted from PDF source: {spec.path}")
    return {"pageCount": len(pdf.pages), "sections": sections}


def load_source(spec: SourceSpec) -> LoadedSource:
    if spec.type == "portfolio-json":
        try:
            content = json.loads(spec.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise ValueError(f"Could not parse portfolio JSON: {spec.path}") from error
    elif spec.type == "pdf":
        content = _extract_pdf(spec)
    else:
        raise ValueError(f"Unsupported source type '{spec.type}' for {spec.id}.")

    return LoadedSource(spec=spec, sha256=_sha256(spec.path), content=content)
