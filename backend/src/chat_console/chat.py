"""POST /api/chat and POST /api/chat/approve — the SSE chat endpoints.

Placeholder — filled in at M1 (single-turn chat + LM Studio) and M2 (the approval relay
described in PROJECT6_SCOPE.md section 4: the backend never approves a confirmation on
the model's behalf; approval_needed suspends the turn until the frontend answers).

Conversation state in M1 is in-memory, keyed by conversation_id (PROJECT6_SCOPE.md
section 9, decision 2); persistence is explicitly out of scope for now.
"""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/api/chat", tags=["chat"])

# M1: POST "" -> SSE stream of {token, tool_call, tool_result, chart, approval_needed, done}
# M2: POST "/approve" -> re-calls the pending tool with {confirmation_token, user_reply}
