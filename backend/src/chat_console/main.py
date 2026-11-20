"""FastAPI entrypoint.

M0: app factory + CORS + GET /health. The /api/chat routes described in
PROJECT6_SCOPE.md section 6 land in M1 (chat.py) and M2 (approval flow).
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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

    return app


app = create_app()


def run() -> None:
    """Entry point for `chat-console-api` (uvicorn, dev reload off by default)."""
    import uvicorn

    uvicorn.run("chat_console.main:app", host="0.0.0.0", port=8000)


if __name__ == "__main__":
    run()
