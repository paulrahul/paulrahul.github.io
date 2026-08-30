"""Build the portfolio chatbot's inspectable local retrieval artifacts."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .loaders import load_source, load_source_specs
from .normalizers import normalise_source


SCHEMA_VERSION = 1
DEFAULT_MODEL = "openai/text-embedding-3-small"
DEFAULT_MAX_WORDS = 220
DEFAULT_OVERLAP_WORDS = 30


def _chat_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _repository_root() -> Path:
    return _chat_root().parent


def _atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as temporary:
        temporary.write(content)
        temporary_path = Path(temporary.name)
    temporary_path.replace(path)


def _atomic_save_numpy(path: Path, vectors: Any) -> None:
    import numpy as np

    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(suffix=".npy", dir=path.parent, delete=False) as temporary:
        temporary_path = Path(temporary.name)
    np.save(temporary_path, vectors)
    temporary_path.replace(path)


def _load_reusable_vectors(output_dir: Path, model: str, *, full_rebuild: bool):
    import numpy as np

    if full_rebuild:
        return {}, 0
    chunks_path = output_dir / "chunks.json"
    vectors_path = output_dir / "embeddings.npy"
    manifest_path = output_dir / "index-manifest.json"
    paths = (chunks_path, vectors_path, manifest_path)
    if not any(path.exists() for path in paths):
        return {}, 0
    if not all(path.is_file() for path in paths):
        return {}, 0

    try:
        chunks_document = json.loads(chunks_path.read_text(encoding="utf-8"))
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        vectors = np.load(vectors_path, allow_pickle=False)
    except (OSError, ValueError, json.JSONDecodeError):
        return {}, 0

    old_chunks = chunks_document.get("chunks") if isinstance(chunks_document, dict) else None
    embedding = manifest.get("embedding") if isinstance(manifest, dict) else None
    if not isinstance(old_chunks, list) or not isinstance(embedding, dict):
        return {}, 0
    if embedding.get("model") != model or embedding.get("status") != "created":
        return {}, len(old_chunks)
    if vectors.ndim != 2 or vectors.shape[0] != len(old_chunks):
        return {}, len(old_chunks)

    reusable = {
        str(chunk["contentHash"]): vectors[index]
        for index, chunk in enumerate(old_chunks)
        if isinstance(chunk, dict) and chunk.get("contentHash")
    }
    return reusable, len(old_chunks)


def _create_embeddings(chunks, output_dir: Path, model: str, *, full_rebuild: bool):
    import numpy as np

    from .embeddings import OpenRouterEmbeddingClient

    reusable, previous_count = _load_reusable_vectors(output_dir, model, full_rebuild=full_rebuild)
    reused: dict[int, Any] = {}
    missing_indices: list[int] = []
    for index, chunk in enumerate(chunks):
        vector = reusable.get(str(chunk["contentHash"]))
        if vector is None:
            missing_indices.append(index)
        else:
            reused[index] = vector

    created = None
    request_count = 0
    if missing_indices:
        client = OpenRouterEmbeddingClient(model)
        try:
            raw_vectors, request_count = client.embed_documents([chunks[index]["text"] for index in missing_indices])
            created = np.asarray(raw_vectors, dtype="float32")
        finally:
            client.close()
        if created.ndim != 2 or created.shape[0] != len(missing_indices) or created.shape[1] == 0:
            raise RuntimeError("OpenRouter returned an invalid embedding matrix.")
        norms = np.linalg.norm(created, axis=1, keepdims=True)
        if np.any(norms == 0):
            raise RuntimeError("OpenRouter returned a zero-length embedding.")
        created = created / norms

    if created is not None:
        dimensions = int(created.shape[1])
    elif reused:
        dimensions = len(next(iter(reused.values())))
    else:
        raise RuntimeError("No chunks were available to embed.")

    vectors = np.empty((len(chunks), dimensions), dtype="float32")
    for index, vector in reused.items():
        if len(vector) != dimensions:
            raise ValueError("Reusable embedding dimensions do not match the current index.")
        vectors[index] = vector
    if created is not None:
        for created_index, chunk_index in enumerate(missing_indices):
            vectors[chunk_index] = created[created_index]

    return {
        "vectors": vectors,
        "dimensions": dimensions,
        "reused": len(reused),
        "embedded": len(missing_indices),
        "removed": max(0, previous_count - len(reused)),
        "requestCount": request_count,
    }


def ingest(
    config_path: Path,
    output_dir: Path,
    *,
    model: str = DEFAULT_MODEL,
    max_words: int = DEFAULT_MAX_WORDS,
    overlap_words: int = DEFAULT_OVERLAP_WORDS,
    skip_embeddings: bool = False,
    full_rebuild: bool = False,
) -> dict[str, Any]:
    specs = load_source_specs(config_path, _repository_root())
    sources = [load_source(spec) for spec in specs]
    chunks: list[dict[str, Any]] = []
    chunk_counts_by_source: dict[str, int] = {}
    for source in sources:
        source_chunks = normalise_source(
            source,
            max_words=max_words,
            overlap_words=overlap_words,
        )
        if not source_chunks:
            raise ValueError(
                f"Source '{source.spec.id}' produced no chunks. Check its loader and source configuration."
            )
        for number, chunk in enumerate(source_chunks, start=1):
            text = chunk.get("text") if isinstance(chunk, dict) else None
            if not isinstance(text, str) or not text.strip():
                raise ValueError(
                    f"Source '{source.spec.id}' produced an empty chunk at position {number}."
                )
            if chunk.get("sourceId") != source.spec.id:
                raise ValueError(
                    f"Source '{source.spec.id}' produced a chunk with mismatched source metadata."
                )
        chunk_counts_by_source[source.spec.id] = len(source_chunks)
        chunks.extend(source_chunks)
    if not chunks:
        raise ValueError("No chunks were generated from the configured sources.")
    chunk_ids = [chunk["id"] for chunk in chunks]
    if len(chunk_ids) != len(set(chunk_ids)):
        raise ValueError("The generated index contains duplicate chunk ids.")

    embedding: dict[str, Any] = {
        "model": model,
        "normalized": True,
        "status": "skipped" if skip_embeddings else "created",
    }
    vectors = None
    if skip_embeddings:
        embedding.update({"reusedChunks": 0, "embeddedChunks": 0, "removedChunks": 0, "requestCount": 0})
    else:
        result = _create_embeddings(chunks, output_dir, model, full_rebuild=full_rebuild)
        vectors = result.pop("vectors")
        embedding.update(
            {
                "dimensions": result["dimensions"],
                "reusedChunks": result["reused"],
                "embeddedChunks": result["embedded"],
                "removedChunks": result["removed"],
                "requestCount": result["requestCount"],
            }
        )

    manifest = {
        "schemaVersion": SCHEMA_VERSION,
        "createdAt": datetime.now(UTC).isoformat(),
        "chunkCount": len(chunks),
        "chunkCountsByKind": {
            kind: sum(chunk["kind"] == kind for chunk in chunks)
            for kind in sorted({str(chunk["kind"]) for chunk in chunks})
        },
        "chunkCountsBySource": chunk_counts_by_source,
        "chunking": {"maxWords": max_words, "overlapWords": overlap_words},
        "embedding": embedding,
        "sources": [
            {
                "id": source.spec.id,
                "type": source.spec.type,
                "path": source.spec.relative_path,
                "title": source.spec.title,
                "url": source.spec.url,
                "sha256": source.sha256,
            }
            for source in sources
        ],
    }

    chunks_document = {"schemaVersion": SCHEMA_VERSION, "language": "en", "chunks": chunks}
    _atomic_write_text(output_dir / "chunks.json", json.dumps(chunks_document, indent=2, ensure_ascii=False) + "\n")
    if vectors is not None:
        _atomic_save_numpy(output_dir / "embeddings.npy", vectors)
    _atomic_write_text(output_dir / "index-manifest.json", json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build portfolio chatbot retrieval artifacts.")
    parser.add_argument(
        "--config",
        type=Path,
        default=_chat_root() / "ingestion" / "sources.json",
        help="JSON file listing approved source documents.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=_chat_root() / "data",
        help="Directory for generated retrieval artifacts.",
    )
    parser.add_argument(
        "--model",
        default=os.getenv("PORTFOLIO_EMBEDDING_MODEL", DEFAULT_MODEL),
        help="OpenRouter embedding model.",
    )
    parser.add_argument("--max-words", type=int, default=DEFAULT_MAX_WORDS)
    parser.add_argument("--overlap-words", type=int, default=DEFAULT_OVERLAP_WORDS)
    parser.add_argument("--skip-embeddings", action="store_true")
    parser.add_argument("--full-rebuild", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    manifest = ingest(
        args.config,
        args.output,
        model=args.model,
        max_words=args.max_words,
        overlap_words=args.overlap_words,
        skip_embeddings=args.skip_embeddings,
        full_rebuild=args.full_rebuild,
    )
    print(f"Indexed {len(manifest['sources'])} sources into {manifest['chunkCount']} chunks.")
    print(
        "Chunks by kind: "
        + ", ".join(
            f"{kind}={count}"
            for kind, count in manifest["chunkCountsByKind"].items()
        )
    )
    print(
        "Chunks by source: "
        + ", ".join(
            f"{source_id}={count}"
            for source_id, count in manifest["chunkCountsBySource"].items()
        )
    )
    print(f"Wrote {args.output / 'chunks.json'}")
    print(f"Wrote {args.output / 'index-manifest.json'}")
    if manifest["embedding"]["status"] == "created":
        print(f"Wrote {args.output / 'embeddings.npy'}")
        print(
            "Embedding work: "
            f"{manifest['embedding']['embeddedChunks']} created, "
            f"{manifest['embedding']['reusedChunks']} reused, "
            f"{manifest['embedding']['removedChunks']} removed."
        )
    else:
        print("Embeddings skipped; rerun without --skip-embeddings to create embeddings.npy.")


if __name__ == "__main__":
    main()
