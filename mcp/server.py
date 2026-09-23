"""FastMCP server exposing Rahul's portfolio data (data.json) as MCP tools."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

# Import the real "mcp" SDK package before touching sys.path below, so it's
# already cached in sys.modules and can't be shadowed by this directory
# (also named "mcp") once the repo root is appended to the path.
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from starlette.requests import Request
from starlette.responses import HTMLResponse

def _find_repo_root(start: Path) -> Path:
    """Locate the directory containing lib/, searching upward from `start`.

    Not always one fixed number of parents away: locally server.py sits nested
    inside mcp/, so lib/ is one level up. Deployed on Vercel, the Root
    Directory's contents are flattened to the function bundle's root, so
    server.py's own directory *is* the bundle root and lib/ (if included) may
    sit right alongside it instead of one level up.
    """
    for candidate in (start, *start.parents):
        if (candidate / "lib" / "loader.py").is_file():
            return candidate
    raise RuntimeError(f"Could not locate the 'lib' package searching upward from {start}")


APP_DIR = Path(__file__).resolve().parent
REPO_ROOT = _find_repo_root(APP_DIR)
# Appended (not inserted at index 0) so site-packages resolve first; avoids this
# directory ever shadowing a same-named third-party package such as "mcp" itself.
if str(REPO_ROOT) not in sys.path:
    sys.path.append(str(REPO_ROOT))

from lib import loader  # noqa: E402


def _transport_security() -> TransportSecuritySettings | None:
    """Opt-in override for local tunnel testing (ngrok/cloudflared).

    The SDK's default DNS-rebinding protection only allows Host headers of
    "localhost"/"127.0.0.1", which rejects requests arriving through a tunnel
    domain. Leave PORTFOLIO_MCP_DISABLE_DNS_REBINDING_PROTECTION unset in any
    real deployment; returning None here keeps the SDK's own default behavior.
    """
    disabled = os.getenv(
        "PORTFOLIO_MCP_DISABLE_DNS_REBINDING_PROTECTION", ""
    ).strip().lower() in ("1", "true", "yes")
    if not disabled:
        return None
    return TransportSecuritySettings(enable_dns_rebinding_protection=False)


mcp = FastMCP("Rahul Paul Portfolio", transport_security=_transport_security())


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

LANDING_PAGE_HTML = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <title>Rahul Paul Portfolio &mdash; MCP server</title>
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <style>
      body { font-family: sans-serif; max-width: 40em; margin: 4em auto; padding: 0 1.5em; line-height: 1.5; color: #2d2d2d; }
      code { background: #f0f0f0; padding: 0.15em 0.4em; border-radius: 4px; }
      a { color: #6b9fc9; }
    </style>
  </head>
  <body>
    <h1>Rahul Paul Portfolio &mdash; MCP server</h1>
    <p>This is an MCP (Model Context Protocol) server exposing Rahul Paul's portfolio
      data as tools: <code>overview</code>, <code>projects</code>, <code>skills</code>,
      <code>experience</code>, <code>education</code>, <code>patents</code>.</p>
    <p>Connect an MCP client (Claude Desktop, Claude Code, etc.) to the streamable-HTTP
      endpoint at <code>/mcp</code>.</p>
    <p>See <a href="https://github.com/paulrahul/paulrahul.github.io">the source</a>
      for details.</p>
  </body>
</html>
"""


async def _landing_page(request: Request) -> HTMLResponse:
    return HTMLResponse(LANDING_PAGE_HTML)


app.add_route("/", _landing_page, methods=["GET"])


__all__ = ["app", "mcp"]
