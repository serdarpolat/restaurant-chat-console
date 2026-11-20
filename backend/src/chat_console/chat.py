"""POST /api/chat — a single chat turn as an SSE stream.

M1 scope: one user message in, one assistant answer out, with real tool calls against
restaurant-mcp-server in between. No approval relay yet (M2) and no charts yet (M3): a
confirmation-gated tool (void_order_item, cancel_order, pay_order, record_stock_purchase)
just returns its preview text as an ordinary tool result here — nothing is approved on the
model's behalf, nothing executes, exactly as if no one had answered the preview yet. M2
turns that preview into a real approval_needed event the frontend can act on.

Conversation history is in-memory, keyed by conversation_id (PROJECT6_SCOPE.md section 9,
decision 2) — lost on backend restart; persistence is out of scope for now.
"""

from __future__ import annotations

import json
import logging
from collections import defaultdict
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from chat_console.llm_client import LlmClient, visible_text
from chat_console.mcp_client import McpClient
from chat_console.settings import get_settings

router = APIRouter(prefix="/api/chat", tags=["chat"])
logger = logging.getLogger(__name__)

MAX_STEPS = 10
SUMMARY_MAX_CHARS = 400

# conversation_id -> plain {role, content} turns (user/assistant only — tool-call
# bookkeeping is rebuilt fresh every turn, not replayed as history).
_HISTORY: dict[str, list[dict[str, str]]] = defaultdict(list)

EVAL_PROTOCOL = (
    "You assist the restaurant staff through a chat UI. Answer in the user's language.\n"
    "Once a tool result comes back, it is already in hand — write the real answer using\n"
    "that data right away in the same turn. Never end with a placeholder like 'please\n"
    "wait' or 'fetching the data', and never promise an answer you have not given yet.\n"
)


class ChatRequest(BaseModel):
    conversation_id: str
    message: str


def _sse(event: str, data: dict[str, Any]) -> dict[str, str]:
    return {"event": event, "data": json.dumps(data, ensure_ascii=False)}


def _summarize(text: str) -> str:
    """A tool result for the UI card — a summary, not the raw JSON (API contract, section 6)."""
    flat = " ".join(text.split())
    if len(flat) <= SUMMARY_MAX_CHARS:
        return flat
    return flat[: SUMMARY_MAX_CHARS - 1].rstrip() + "…"


def _word_chunks(text: str, size: int = 40) -> list[str]:
    """Split the final answer into word-grouped pieces for a typing effect.

    This is not token-level streaming from LM Studio (that would mean parsing tool_call
    argument deltas across chunks, which buys nothing until the approval/chart milestones
    need the extra complexity) — just the final, already-complete answer, chunked so the
    `token` SSE event in the API contract still arrives "parça parça" as specified.
    """
    words = text.split(" ")
    chunks, current = [], ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) > size and current:
            chunks.append(current + " ")
            current = word
        else:
            current = candidate
    if current:
        chunks.append(current)
    return chunks or [text]


def _tool_specs(tools_meta: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "type": "function",
            "function": {
                "name": t["name"],
                "description": t["description"],
                "parameters": t["input_schema"],
            },
        }
        for t in tools_meta
    ]


@router.post("")
async def post_chat(req: ChatRequest) -> EventSourceResponse:
    settings = get_settings()
    history = _HISTORY[req.conversation_id]
    history.append({"role": "user", "content": req.message})

    async def events():
        llm = LlmClient(settings.llm_base_url, settings.llm_model)
        try:
            async with McpClient(settings.mcp_server_url) as mcp:
                tools_meta = await mcp.list_tools()
                tools = _tool_specs(tools_meta)
                # The server's own instructions, fetched live — not LM Studio's job to
                # forward them (it doesn't), ours to ask for them and pass them on.
                system = (mcp.instructions or "") + "\n" + EVAL_PROTOCOL
                messages: list[dict[str, Any]] = [
                    {"role": "system", "content": system},
                    *history,
                ]

                for _ in range(MAX_STEPS):
                    data = await llm.complete(messages, tools)
                    message = data["choices"][0]["message"]
                    tool_calls = message.get("tool_calls") or []
                    messages.append(
                        {
                            "role": "assistant",
                            "content": message.get("content") or "",
                            **({"tool_calls": tool_calls} if tool_calls else {}),
                        }
                    )

                    if not tool_calls:
                        text = visible_text(message.get("content"))
                        history.append({"role": "assistant", "content": text})
                        for chunk in _word_chunks(text):
                            yield _sse("token", {"text": chunk})
                        break

                    for tc in tool_calls:
                        name = tc["function"]["name"]
                        raw = tc["function"].get("arguments") or "{}"
                        try:
                            args = json.loads(raw) if isinstance(raw, str) else dict(raw)
                        except json.JSONDecodeError:
                            args = {}
                        yield _sse("tool_call", {"name": name, "args": args})

                        result = await mcp.call_tool(name, args)
                        yield _sse(
                            "tool_result",
                            {
                                "name": name,
                                "ok": not result["is_error"],
                                "summary": _summarize(result["text"]),
                            },
                        )
                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tc.get("id", ""),
                                "content": result["text"],
                            }
                        )
                else:
                    yield _sse(
                        "tool_result",
                        {
                            "name": "_system",
                            "ok": False,
                            "summary": f"no final answer after {MAX_STEPS} steps",
                        },
                    )
        except Exception as exc:  # one bad turn must not crash the stream; logged below
            # Also log server-side: the SSE event is the only other place this reaches,
            # and a dropped/stale frontend connection shouldn't mean the error vanishes
            # entirely.
            logger.exception("chat turn failed (conversation_id=%s)", req.conversation_id)
            yield _sse(
                "tool_result",
                {"name": "_system", "ok": False, "summary": f"{type(exc).__name__}: {exc}"},
            )
        finally:
            await llm.aclose()
            yield _sse("done", {})

    return EventSourceResponse(events())
