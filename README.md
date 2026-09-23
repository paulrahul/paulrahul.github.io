# Backend services

Three small Python services sit alongside the static site:

- `chat/` — RAG-based chat assistant (FastAPI + OpenAI Agents SDK)
- `api/` — REST API exposing `data.json` (overview, projects, skills, experience, education, patents)
- `mcp/` — MCP server exposing the same data as tools (FastMCP, streamable-HTTP transport)

`api/` and `mcp/` each carry an identical copy of the `lib/` data loader (`api/lib/`, `mcp/lib/`). If you change one, copy it to the other. The loader reads the repo-root `data.json` when it can find it (local dev, a VM checkout). Otherwise it fetches the published copy from `https://paulrahul.github.io/data.json`.

## Deploying `api/` and `mcp/` to Vercel

Each is its own Vercel project: **Add New → Project → import this repo → set Root Directory to `api` or `mcp`**. Vercel only bundles files inside that Root Directory. That's why `lib/` is vendored into each service, and why on Vercel `data.json` comes from the published site: changes to it reach the API/MCP only after GitHub Pages redeploys.

## Chat server (`chat/`)

```bash
cd chat
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in OPENROUTER_API_KEY at minimum
uvicorn app:app --reload --port 8000
```

Open http://localhost:8000.

## Portfolio API (`api/`)

```bash
cd api
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --reload --port 8010
```

Try it: `curl http://localhost:8010/overview`

## Portfolio MCP server (`mcp/`)

```bash
cd mcp
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn server:app --reload --port 8020
```

FastMCP mounts the streamable-HTTP endpoint at `/mcp` by default, so point an MCP client at `http://localhost:8020/mcp`.

Claude Desktop custom connectors require `https://`, so to test one against a local server, expose it through a tunnel (e.g. `cloudflared tunnel --url http://localhost:8020`) and use the tunnel URL plus `/mcp`.
