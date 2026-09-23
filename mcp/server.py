"""FastMCP server exposing Rahul's portfolio data (data.json) as MCP tools."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import HTMLResponse

from lib import loader

MCP_PUBLIC_URL = "https://mcp-rho-azure.vercel.app"
MCP_ENDPOINT_URL = f"{MCP_PUBLIC_URL}/mcp"

# uvicorn/Vercel handle binding; a non-localhost host just stops FastMCP from
# enabling its localhost-only Host-header check, which would reject public requests.
mcp = FastMCP("Rahul Paul Portfolio", host="0.0.0.0")


@mcp.tool()
def overview() -> dict[str, Any]:
    """High-level overview: location, work mode, availability, preferred roles/domains, work authorization."""
    return loader.get_overview()


@mcp.tool()
def projects() -> list[dict[str, Any]]:
    """Rahul's side/personal projects, with descriptions, tech stack, and links."""
    return loader.get_projects()


@mcp.tool()
def skills() -> dict[str, Any]:
    """Rahul's skills, grouped by category (Languages, Frontend, Backend, AI & Agents, Cloud & Infra)."""
    return loader.get_skills()


@mcp.tool()
def experience() -> list[dict[str, Any]]:
    """Rahul's work experience / employment history, most recent first."""
    return loader.get_experience()


@mcp.tool()
def education() -> list[dict[str, Any]]:
    """Rahul's educational qualifications."""
    return loader.get_education()


@mcp.tool()
def patents() -> dict[str, Any]:
    """Patents Rahul is named on."""
    return loader.get_patents()


app = mcp.streamable_http_app()

MCP_CLIENT_CONFIG = f"""{{
  "mcpServers": {{
    "rahul-paul-portfolio": {{
      "url": "{MCP_ENDPOINT_URL}"
    }}
  }}
}}"""

LANDING_PAGE_HTML = f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <title>Rahul Paul Portfolio &mdash; MCP server</title>
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <style>
      body {{ font-family: sans-serif; max-width: 40em; margin: 4em auto; padding: 0 1.5em; line-height: 1.5; color: #2d2d2d; }}
      code {{ background: #f0f0f0; padding: 0.15em 0.4em; border-radius: 4px; }}
      a {{ color: #6b9fc9; }}
      pre {{ background: #f0f0f0; padding: 1em; border-radius: 8px; overflow-x: auto; position: relative; }}
      pre code {{ background: none; padding: 0; }}
      .copy-btn {{ position: absolute; top: 0.6em; right: 0.6em; font-size: 0.8rem; padding: 0.3em 0.7em; border: 1px solid #ccc; border-radius: 6px; background: #fff; cursor: pointer; }}
      .copy-btn:hover {{ background: #eee; }}
    </style>
  </head>
  <body>
    <h1>Rahul Paul Portfolio &mdash; MCP server</h1>
    <p>This is an MCP (Model Context Protocol) server exposing Rahul Paul's portfolio
      data as tools: <code>overview</code>, <code>projects</code>, <code>skills</code>,
      <code>experience</code>, <code>education</code>, <code>patents</code>.</p>
    <p>Connect an MCP client (Claude Desktop, Claude Code, etc.) to the streamable-HTTP
      endpoint at <code><a href="{MCP_ENDPOINT_URL}">{MCP_ENDPOINT_URL}</a></code>.</p>

    <h2>Client config</h2>
    <p>Paste this into your MCP client's config (e.g. Claude Desktop, Claude Code, Cursor):</p>
    <pre><button class="copy-btn" data-copy-target="mcp-config" onclick="navigator.clipboard.writeText(document.getElementById('mcp-config').textContent); this.textContent = 'Copied!'; setTimeout(() => this.textContent = 'Copy', 1500);">Copy</button><code id="mcp-config">{MCP_CLIENT_CONFIG}</code></pre>

    <p>See <a href="https://github.com/paulrahul/paulrahul.github.io">the source</a>
      for details.</p>
  </body>
</html>
"""


async def _landing_page(request: Request) -> HTMLResponse:
    return HTMLResponse(LANDING_PAGE_HTML)


app.add_route("/", _landing_page, methods=["GET"])


__all__ = ["app", "mcp"]
