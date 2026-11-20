# restaurant-chat-console

A Claude-like chat console over `restaurant-mcp-server`: a restaurant employee asks in
natural language, a local LM Studio model answers using the server's 20 MCP tools
(reports, inventory, orders), the console draws charts automatically for the tools that
support it, and any action that needs approval (voiding an item, cancelling an order,
taking a payment, recording a stock purchase) waits for a real click before it runs.

> **Status: M0 — skeleton only.** Backend exposes `GET /health`; frontend renders a
> single page that checks it. No chat yet. See `PROJECT6_SCOPE.md` for the milestone
> plan (M0 → M1 chat → M2 approval flow → M3 charts → M4 polish + demo).

> ⚠️ **Demo only.** No authentication anywhere in this stack (console, backend, or the
> `restaurant-mcp-server` it talks to). Don't expose these ports beyond localhost.

## Run it

```bash
docker compose up
```

- Chat UI: http://localhost:3000
- Backend health check: http://localhost:8000/health

LM Studio must be running on the host machine (not in this compose stack) with a model
loaded and its local server started, reachable at `http://localhost:1234` — the backend
talks to it via `host.docker.internal`.

## Repo layout

```
backend/   FastAPI (chat.py, mcp_client.py, llm_client.py, charts.py)
frontend/  Nuxt 4 chat UI
docker-compose.yml   backend + frontend + restaurant-mcp-server (pinned via git, see below)
```

`restaurant-mcp-server` is never modified or vendored here — `docker-compose.yml` builds
it straight from its own repo, pinned to one commit, the same pattern
`restaurant-ai-analyst` (a sibling project) uses for its data dependency.

## Local development (without Docker)

```bash
# backend
cd backend && uv venv .venv && source .venv/bin/activate
uv pip install -e ".[dev]"
pytest && ruff check . && ruff format --check .
chat-console-api   # http://localhost:8000

# frontend
cd frontend && npm install
npm run dev        # http://localhost:3000
```
