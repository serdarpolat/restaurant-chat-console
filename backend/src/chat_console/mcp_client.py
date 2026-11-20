"""MCP client for restaurant-mcp-server.

Placeholder — filled in at M1. Will hold a real MCP client (not a mock) that talks to
restaurant-pos-mcp --http at settings.mcp_server_url, lists its 20 tools, and calls them
on the model's behalf. See PROJECT6_SCOPE.md section 3.

restaurant-mcp-server itself is never modified or vendored here — it is reached only
through the MCP protocol, pinned as a dependency at the commit docker-compose.yml builds.
"""

from __future__ import annotations


class McpClient:
    """Not yet implemented (M1)."""

    def __init__(self, server_url: str) -> None:
        self.server_url = server_url

    async def list_tools(self) -> list[dict]:
        raise NotImplementedError("M1: connect to restaurant-pos-mcp --http and list tools")

    async def call_tool(self, name: str, arguments: dict) -> dict:
        raise NotImplementedError("M1: call an MCP tool and return its result")
