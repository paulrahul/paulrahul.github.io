# Portfolio chatbot ingestion

Run ingestion whenever `data.json`, `resume.pdf`, or the configured sources change.
It rebuilds the retrieval chunks and creates embeddings for changed content while
reusing unchanged embeddings.

## One-time setup

From the repository root:

```sh
cd chat
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

Create `chat/.env` if it does not already exist:

```dotenv
OPENROUTER_API_KEY=your_openrouter_api_key
```

The default embedding model is `openai/text-embedding-3-small`. To override it,
also set:

```dotenv
PORTFOLIO_EMBEDDING_MODEL=provider/model-name
```

## Ingest updated portfolio data

From the repository root:

```sh
cd chat
.venv/bin/python -m ingestion.ingest
```

The configured sources are listed in `ingestion/sources.json`. They currently
include the repository-level `data.json` and `resume.pdf`.

The command updates these deployment artifacts:

- `data/chunks.json`
- `data/embeddings.npy`
- `data/index-manifest.json`

Review and commit all three files together with the source changes, then redeploy
or restart the chat server so it loads the new index.

## Full rebuild

Normal ingestion reuses embeddings for chunks whose content has not changed. To
force every chunk to be embedded again:

```sh
cd chat
.venv/bin/python -m ingestion.ingest --full-rebuild
```

This uses additional embedding API requests and is normally unnecessary for
small edits to `data.json`.

## Other options

See all supported arguments:

```sh
cd chat
.venv/bin/python -m ingestion.ingest --help
```

Use `--skip-embeddings` only to inspect generated chunks during development. It
does not produce a deployable retrieval index.
