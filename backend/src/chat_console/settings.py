"""Runtime configuration, all overridable via environment variables.

Kept in one place so M1 (LM Studio client) and the MCP client can both read it without
each module inventing its own env var names.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    # restaurant-mcp-server, run with `restaurant-pos-mcp --http` (see docker-compose.yml).
    mcp_server_url: str = os.environ.get("MCP_SERVER_URL", "http://localhost:8001/mcp")

    # LM Studio's OpenAI-compatible endpoint.
    llm_base_url: str = os.environ.get("LLM_BASE_URL", "http://localhost:1234/v1")
    llm_model: str = os.environ.get("LLM_MODEL", "magistral-small-2509")

    # CORS: the Nuxt dev server by default; override in docker-compose for the built frontend.
    cors_origins: tuple[str, ...] = tuple(
        os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(",")
    )


def get_settings() -> Settings:
    return Settings()
