"""FastAPI entrypoint.

M0: app factory + CORS + GET /health. M1 adds POST /api/chat (chat.py) — a single-turn
SSE chat stream backed by a real MCP client and a real LM Studio client. The approval
relay (POST /api/chat/approve) described in PROJECT6_SCOPE.md section 6 lands in M2.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from chat_console import chat
from chat_console.settings import get_settings

__version__ = "0.1.0"


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="restaurant-chat-console backend",
        version=__version__,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok", "version": __version__}

    app.include_router(chat.router)

    return app


app = create_app()


def run() -> None:
    """Entry point for `chat-console-api` (uvicorn, dev reload off by default)."""
    import uvicorn

    uvicorn.run("chat_console.main:app", host="0.0.0.0", port=8000)


if __name__ == "__main__":
    run()
