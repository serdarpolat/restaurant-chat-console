"""LM Studio client — OpenAI-compatible /v1/chat/completions, one step at a time.

Ported from restaurant-mcp-server's eval harness (evals/agent.py::OpenAICompatibleAgent),
the same provider Serdar already measured against this exact server. The eval agent runs a
whole multi-step tool-calling loop per case; here chat.py owns the loop instead (so it can
emit an SSE event — tool_call, tool_result — between steps), and this client only knows how
to ask the model for one step and clean up its answer.
"""

from __future__ import annotations

import asyncio
import re
from typing import Any

import httpx

_THINK = re.compile(r"<think>.*?</think>", re.DOTALL)


def visible_text(text: str | None) -> str:
    """Drop <think>...</think> blocks some local reasoning models put in the answer."""
    text = _THINK.sub("", text or "")
    if "</think>" in text:  # opening tag was in the prompt template, closing one in the answer
        text = text.split("</think>", 1)[1]
    return text.strip()


class LlmClient:
    def __init__(
        self,
        base_url: str,
        model: str,
        max_tokens: int = 4096,
        timeout: float = 600,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.model = model
        self.max_tokens = max_tokens
        self.http = httpx.AsyncClient(
            base_url=base_url.rstrip("/") + "/", timeout=timeout, transport=transport
        )

    async def aclose(self) -> None:
        await self.http.aclose()

    async def complete(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> dict:
        """One /chat/completions call (no streaming — see chat.py for why). Retries once per
        5s-10s-...-40s on 429 (free/local rate limits), same backoff as the eval agent."""
        body = {
            "model": self.model,
            "messages": messages,
            "tools": tools,
            "tool_choice": "auto" if tools else "none",
            "max_tokens": self.max_tokens,
        }
        for attempt in range(5):
            response = await self.http.post("chat/completions", json=body)
            if response.status_code == 429 and attempt < 4:
                await asyncio.sleep(float(response.headers.get("retry-after", 10 * (attempt + 1))))
                continue
            if response.is_error:
                raise RuntimeError(f"HTTP {response.status_code}: {response.text[:500]}")
            return response.json()
        raise RuntimeError("rate limited")
