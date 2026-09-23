# Backend services

Three small Python services sit alongside the static site:

- `chat/` — RAG-based chat assistant (FastAPI + OpenAI Agents SDK)
- `api/` — REST API exposing `data.json` (overview, projects, skills, experience, education, patents)
- `mcp/` — MCP server exposing the same data as tools (FastMCP, streamable-HTTP transport)

`api/` and `mcp/` both read through the shared `lib/` package, so `data.json` has one source of truth.

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

To test through a tunnel (e.g. Claude Desktop custom connectors require `https://`, so a plain `http://localhost` URL won't work — use `cloudflared tunnel --url http://localhost:8020` or similar), the SDK's default DNS-rebinding protection will reject the tunnel's Host header. Disable it for that run only:

```bash
PORTFOLIO_MCP_DISABLE_DNS_REBINDING_PROTECTION=1 uvicorn server:app --reload --port 8020
```

Leave this unset for any real deployment.
