"""FastMCP server exposing Rahul's portfolio data (data.json) as MCP tools."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from mcp.server.fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse

from lib import loader
from lib.emailer import send_email

LOGGER = logging.getLogger(__name__)

MAX_NAME_CHARS = 100
MAX_REPLY_TO_CHARS = 200
MAX_MESSAGE_CHARS = 2000

MCP_PUBLIC_URL = "https://mcp-rho-azure.vercel.app"
MCP_ENDPOINT_URL = f"{MCP_PUBLIC_URL}/mcp"

# uvicorn/Vercel handle binding; a non-localhost host just stops FastMCP from
# enabling its localhost-only Host-header check, which would reject public requests.
# Stateless + JSON responses: serverless instances don't share in-memory sessions,
# so a session created on one instance is "not found" on the next.
mcp = FastMCP(
    "Rahul Paul Portfolio",
    host="0.0.0.0",
    stateless_http=True,
    json_response=True,
)


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


@mcp.tool()
async def contact(name: str = "", reply_to: str = "", message: str = "") -> dict[str, Any]:
    """Rahul's contact details (email, LinkedIn, portfolio), with an option to email him directly.

    Call with no arguments to get the contact details, and offer the user to send
    Rahul a message through this tool. Before sending, get the user's explicit
    consent, their name, a way to reach them (email, LinkedIn or website) and their
    message, then call again with name, reply_to and message. Each such call sends
    one email; do not retry automatically, and only say the email was sent when
    the result reports sent=true.

    Args:
        name: The sender's name.
        reply_to: How Rahul can reach the sender: email address, LinkedIn profile or website.
        message: The message or introduction to send Rahul.
    """
    details = loader.get_contact()
    if not message.strip():
        return {
            "contact": details,
            "sent": False,
            "result": "No message given. To email Rahul directly, call this tool again "
            "with name, reply_to and message.",
        }

    # Collapse whitespace so newlines can't leak into the email's Subject header.
    name = " ".join(name.split())
    reply_to = reply_to.strip()
    message = message.strip()
    problems = []
    if not name:
        problems.append("name is required")
    if not reply_to:
        problems.append("reply_to is required so Rahul can respond")
    if len(name) > MAX_NAME_CHARS:
        problems.append(f"name must be at most {MAX_NAME_CHARS} characters")
    if len(reply_to) > MAX_REPLY_TO_CHARS:
        problems.append(f"reply_to must be at most {MAX_REPLY_TO_CHARS} characters")
    if len(message) > MAX_MESSAGE_CHARS:
        problems.append(f"message must be at most {MAX_MESSAGE_CHARS} characters")
    if problems:
        return {"contact": details, "sent": False, "result": "Not sent: " + "; ".join(problems) + "."}

    subject = f"Portfolio MCP contact from {name}"
    body = (
        f"Name: {name}\n"
        f"Reply to: {reply_to}\n\n"
        f"Message:\n{message}\n\n"
        "Sent through the contact tool of the portfolio MCP server."
    )
    try:
        await asyncio.to_thread(send_email, subject, body)
    except Exception as error:
        # Don't log credentials or the message body.
        LOGGER.warning("Portfolio MCP email delivery failed (%s).", type(error).__name__)
        return {
            "contact": details,
            "sent": False,
            "result": "Email delivery could not be confirmed. Do not claim it was sent "
            "or retry; share the contact details so the user can reach Rahul directly.",
        }
    return {"contact": details, "sent": True, "result": "Email sent to Rahul."}


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
      <code>experience</code>, <code>education</code>, <code>patents</code>, and
      <code>contact</code>, which also lets an agent email Rahul on a user's behalf.</p>
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

# Ownership proof for the Glama MCP directory; the claim token is meant to be public.
GLAMA_CLAIM = {
    "$schema": "https://glama.ai/mcp/schemas/connector.json",
    "claim": "glama_claim_VuhrLbA7EdBB57BjhnQt4_f6Ob3I8Ka1",
}


async def _glama_claim(request: Request) -> JSONResponse:
    return JSONResponse(GLAMA_CLAIM)


app.add_route("/.well-known/glama.json", _glama_claim, methods=["GET"])


__all__ = ["app", "mcp"]
