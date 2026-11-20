"""LM Studio client (OpenAI-compatible /v1/chat/completions) with a tool-calling loop.

Placeholder — filled in at M1. This is the production, multi-turn, streaming sibling of
evals/agent.py::OpenAICompatibleAgent from restaurant-mcp-server's eval harness (see
PROJECT6_SCOPE.md section 3) — same provider, but driven by chat turns instead of a
single eval case, and streaming tokens back over SSE instead of returning a final string.
"""

from __future__ import annotations

from collections.abc import AsyncIterator


class LlmClient:
    """Not yet implemented (M1)."""

    def __init__(self, base_url: str, model: str) -> None:
        self.base_url = base_url
        self.model = model

    async def stream_chat(self, messages: list[dict], tools: list[dict]) -> AsyncIterator[dict]:
        raise NotImplementedError("M1: stream model tokens + tool_call events")
