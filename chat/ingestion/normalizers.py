"""Convert loaded portfolio sources into stable, embedding-ready chunks."""

from __future__ import annotations

import hashlib
import logging
import re
from collections.abc import Iterable
from typing import Any

from .loaders import LoadedSource


LOGGER = logging.getLogger(__name__)


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "item"


def _values(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def _split_words(text: str, max_words: int, overlap_words: int) -> list[str]:
    words = text.split()
    if len(words) <= max_words:
        return [text]
    parts: list[str] = []
    start = 0
    while start < len(words):
        end = min(len(words), start + max_words)
        parts.append(" ".join(words[start:end]))
        if end == len(words):
            break
        start = end - overlap_words
    return parts


def _chunks(
    source: LoadedSource,
    *,
    record_id: str,
    kind: str,
    heading: str,
    text: str,
    max_words: int,
    overlap_words: int,
    metadata: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for part, chunk_text in enumerate(_split_words(text.strip(), max_words, overlap_words), start=1):
        content_hash = hashlib.sha256(chunk_text.encode("utf-8")).hexdigest()
        chunk_id = record_id if part == 1 else f"{record_id}:part-{part}"
        chunk = {
            "id": chunk_id,
            "sourceId": source.spec.id,
            "sourceType": source.spec.type,
            "sourceTitle": source.spec.title,
            "sourceUrl": source.spec.url,
            "sourcePath": source.spec.relative_path,
            "sourceHash": source.sha256,
            "kind": kind,
            "heading": heading,
            "part": part,
            "text": chunk_text,
            "contentHash": content_hash,
            "wordCount": len(chunk_text.split()),
        }
        if metadata:
            chunk["metadata"] = metadata
        results.append(chunk)
    return results


def _field_label(key: str) -> str:
    words = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", key)
    return words.replace("_", " ").replace("-", " ").strip().capitalize()


def _overview_lines(value: Any, path: str) -> list[str]:
    """Flatten JSON without losing nested labels, qualifiers or list items."""
    if isinstance(value, dict):
        return [
            line
            for key, child in value.items()
            for line in _overview_lines(child, f"{path} — {_field_label(key)}")
        ]
    if isinstance(value, list):
        if all(not isinstance(item, (dict, list)) for item in value):
            items = [
                str(item).strip() if not isinstance(item, bool) else str(item).lower()
                for item in value
                if item is not None and str(item).strip()
            ]
            return [f"{path}: {'; '.join(items)}"] if items else []
        return [
            line
            for number, item in enumerate(value, start=1)
            for line in _overview_lines(item, f"{path} — Item {number}")
        ]
    if value is None or not str(value).strip():
        return []
    text = str(value).lower() if isinstance(value, bool) else str(value).strip()
    return [f"{path}: {text}"]


def _normalise_overview(source: LoadedSource, overview: dict[str, Any], max_words: int, overlap: int):
    lines: list[str] = []
    fields: list[str] = []
    for key, value in overview.items():
        field_lines = _overview_lines(value, _field_label(key))
        if not field_lines:
            LOGGER.warning("Overview field '%s' in '%s' is empty; not indexed.", key, source.spec.id)
            continue
        fields.append(key)
        lines.extend(field_lines)
    if not lines:
        raise ValueError(f"Portfolio overview in '{source.spec.id}' has no indexable information.")
    return _chunks(
        source,
        record_id=f"{source.spec.id}:overview",
        kind="overview",
        heading="Profile overview — current preferences and availability",
        text="Rahul's profile overview:\n" + "\n".join(lines),
        max_words=max_words,
        overlap_words=overlap,
        metadata={"fields": fields},
    )


def _normalise_projects(source: LoadedSource, projects: Iterable[dict[str, Any]], max_words: int, overlap: int):
    chunks: list[dict[str, Any]] = []
    for project in projects:
        title = str(project.get("title") or "Untitled project").strip()
        lines = [f"Project: {title}."]
        if project.get("tagline"):
            lines.append(f"Tagline: {project['tagline']}.")
        descriptions = _values(project.get("description"))
        if descriptions:
            lines.append("Description: " + " ".join(descriptions))
        stack = _values(project.get("stack"))
        if stack:
            lines.append("Technology stack: " + ", ".join(stack) + ".")
        tags = _values(project.get("tags"))
        if tags:
            lines.append("Topics: " + ", ".join(tags) + ".")
        if project.get("sourceUrl"):
            lines.append(f"Source code: {project['sourceUrl']}.")
        if project.get("liveUrl"):
            lines.append(f"Project website: {project['liveUrl']}.")
        chunks.extend(
            _chunks(
                source,
                record_id=f"{source.spec.id}:project:{_slug(title)}",
                kind="project",
                heading=title,
                text="\n".join(lines),
                max_words=max_words,
                overlap_words=overlap,
                metadata={"title": title, "tags": tags, "stack": stack},
            )
        )
    return chunks


def _normalise_skills(source: LoadedSource, skills: dict[str, Any], max_words: int, overlap: int):
    chunks: list[dict[str, Any]] = []
    for category, value in skills.items():
        items = _values(value.get("skills") if isinstance(value, dict) else value)
        text = f"Rahul's {category} skills: {', '.join(items)}."
        chunks.extend(
            _chunks(
                source,
                record_id=f"{source.spec.id}:skills:{_slug(category)}",
                kind="skills",
                heading=f"Skills — {category}",
                text=text,
                max_words=max_words,
                overlap_words=overlap,
                metadata={"category": category, "skills": items},
            )
        )
    return chunks


def _normalise_experience(source: LoadedSource, experiences: Iterable[dict[str, Any]], max_words: int, overlap: int):
    chunks: list[dict[str, Any]] = []
    for experience in experiences:
        company = str(experience.get("company") or "Career break").strip()
        role = str(experience.get("role") or "Role not specified").strip()
        start = str(experience.get("start") or "").strip()
        end = str(experience.get("end") or "").strip()
        lines = [f"Experience: {role} at {company}."]
        if start or end:
            lines.append(f"Period: {start} to {end}.".replace("  ", " "))
        if experience.get("location"):
            lines.append(f"Location: {experience['location']}.")
        if experience.get("description"):
            lines.append(f"Summary: {experience['description']}")
        achievements = _values(experience.get("achievements"))
        if achievements:
            lines.append("Achievements and responsibilities: " + " ".join(achievements))
        tags = _values(experience.get("tags"))
        if tags:
            lines.append("Related skills and topics: " + ", ".join(tags) + ".")
        identifier = _slug(f"{company}-{role}-{start}")
        chunks.extend(
            _chunks(
                source,
                record_id=f"{source.spec.id}:experience:{identifier}",
                kind="experience",
                heading=f"{role} — {company}",
                text="\n".join(lines),
                max_words=max_words,
                overlap_words=overlap,
                metadata={
                    "company": company,
                    "role": role,
                    "start": start,
                    "end": end,
                    "location": str(experience.get("location") or "").strip(),
                    "tags": tags,
                },
            )
        )
    return chunks


def _normalise_portfolio(source: LoadedSource, max_words: int, overlap: int) -> list[dict[str, Any]]:
    document = source.content
    if not isinstance(document, dict):
        raise ValueError("Portfolio JSON must contain an object.")
    unhandled = set(document) - {"overview", "projects", "skills", "experience"}
    if unhandled:
        LOGGER.warning(
            "Portfolio source '%s' has unhandled top-level sections that will NOT be indexed: %s",
            source.spec.id,
            ", ".join(sorted(unhandled)),
        )
    overview_chunks = []
    if "overview" in document:
        overview = document["overview"]
        if not isinstance(overview, dict):
            raise ValueError("Portfolio overview must be an object.")
        overview_chunks = _normalise_overview(source, overview, max_words, overlap)
    projects = document.get("projects")
    skills = document.get("skills")
    experience = document.get("experience")
    if not isinstance(projects, list) or not isinstance(skills, dict) or not isinstance(experience, list):
        raise ValueError("Portfolio JSON must contain projects, skills, and experience sections.")
    return [
        *overview_chunks,
        *_normalise_projects(source, projects, max_words, overlap),
        *_normalise_skills(source, skills, max_words, overlap),
        *_normalise_experience(source, experience, max_words, overlap),
    ]


def _normalise_pdf(source: LoadedSource, max_words: int, overlap: int) -> list[dict[str, Any]]:
    sections = source.content.get("sections") if isinstance(source.content, dict) else None
    if not isinstance(sections, list):
        raise ValueError(f"PDF source '{source.spec.id}' has no extracted sections.")
    chunks: list[dict[str, Any]] = []
    for section in sections:
        key = str(section["key"])
        heading = str(section["heading"])
        chunks.extend(
            _chunks(
                source,
                record_id=f"{source.spec.id}:{_slug(key)}",
                kind="resume",
                heading=heading,
                text=str(section["text"]),
                max_words=max_words,
                overlap_words=overlap,
                metadata={"page": int(section["page"]), "region": str(section["region"])},
            )
        )
    return chunks


def normalise_source(source: LoadedSource, *, max_words: int, overlap_words: int) -> list[dict[str, Any]]:
    if max_words < 1 or overlap_words < 0 or overlap_words >= max_words:
        raise ValueError("Chunking requires max_words > 0 and 0 <= overlap_words < max_words.")
    if source.spec.type == "portfolio-json":
        return _normalise_portfolio(source, max_words, overlap_words)
    if source.spec.type == "pdf":
        return _normalise_pdf(source, max_words, overlap_words)
    raise ValueError(f"Unsupported source type: {source.spec.type}")
