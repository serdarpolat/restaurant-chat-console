"""MCP client for restaurant-mcp-server, reached over Streamable HTTP.

A thin wrapper around `mcp.Client` (MCP Python SDK 2.x — the same client restaurant-
mcp-server's own eval harness uses, evals/harness.py::ToolSession, just over a real HTTP
connection to `restaurant-pos-mcp --http` instead of in-process). restaurant-mcp-server
is never imported or vendored here; this only speaks the MCP protocol to it.

Unlike LM Studio (which drops the server's `instructions`), we are a real MCP client, so
`instructions` is exposed and the caller is expected to put it in the system prompt
themselves — see chat.py.
"""

from __future__ import annotations

import json
from types import TracebackType
from typing import Any, Self

from mcp import Client


class McpClient:
    def __init__(self, server_url: str) -> None:
        self.server_url = server_url
        self._client = Client(server_url)

    async def __aenter__(self) -> Self:
        await self._client.__aenter__()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self._client.__aexit__(exc_type, exc, tb)

    @property
    def instructions(self) -> str | None:
        """The server's own system-prompt text (restaurant-mcp-server's INSTRUCTIONS),
        fetched live at connect time rather than copied into this repo, so it never goes
        stale when Project 1 changes it."""
        return self._client.instructions

    async def list_tools(self) -> list[dict[str, Any]]:
        listed = (await self._client.list_tools()).tools
        return [
            {"name": t.name, "description": t.description or "", "input_schema": t.input_schema}
            for t in listed
        ]

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Call one tool. Returns {"is_error": bool, "text": str} — never raises on a
        protocol/validation error, so one bad call doesn't crash the chat turn (matches
        evals/harness.py::ToolSession.call, which this mirrors).
        """
        try:
            result = await self._client.call_tool(name, arguments)
        except Exception as exc:  # noqa: BLE001 - surfaced to the model as a tool error instead
            return {"is_error": True, "text": f"{type(exc).__name__}: {exc}"}

        payload = result.structured_content
        if payload is not None and not result.is_error:
            if set(payload) == {"result"}:
                payload = payload["result"]
            text = json.dumps(payload, ensure_ascii=False, default=str)
        else:
            text = "\n".join(getattr(c, "text", "") for c in result.content)
        return {"is_error": bool(result.is_error), "text": text}
