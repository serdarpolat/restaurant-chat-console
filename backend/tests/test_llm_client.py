import httpx
import pytest

from chat_console.llm_client import LlmClient, visible_text


def _client(handler) -> LlmClient:
    return LlmClient(
        "http://fake/v1", "test-model", timeout=5, transport=httpx.MockTransport(handler)
    )


async def test_complete_returns_json_body() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/chat/completions"
        return httpx.Response(200, json={"choices": [{"message": {"content": "hi"}}]})

    client = _client(handler)
    try:
        data = await client.complete([{"role": "user", "content": "hi"}], tools=[])
        assert data["choices"][0]["message"]["content"] == "hi"
    finally:
        await client.aclose()


async def test_complete_retries_once_on_429_then_succeeds() -> None:
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] == 1:
            return httpx.Response(429, headers={"retry-after": "0"})
        return httpx.Response(200, json={"choices": [{"message": {"content": "ok"}}]})

    client = _client(handler)
    try:
        data = await client.complete([], tools=[])
        assert calls["n"] == 2
        assert data["choices"][0]["message"]["content"] == "ok"
    finally:
        await client.aclose()


async def test_complete_raises_after_repeated_429() -> None:
    # Ported as-is from evals/agent.py::OpenAICompatibleAgent._complete: on the 5th attempt
    # `attempt < 4` is false, so it falls through to the generic "is_error" branch and
    # raises "HTTP 429: ..." — the trailing `raise RuntimeError("rate limited")` after the
    # loop is unreachable in both the original and this port. Documented here, not "fixed",
    # to keep behavior identical to the version Serdar already measured against LM Studio.
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(429, headers={"retry-after": "0"})

    client = _client(handler)
    try:
        with pytest.raises(RuntimeError, match="HTTP 429"):
            await client.complete([], tools=[])
        assert calls["n"] == 5
    finally:
        await client.aclose()


async def test_complete_raises_on_http_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="boom")

    client = _client(handler)
    try:
        with pytest.raises(RuntimeError, match="HTTP 500"):
            await client.complete([], tools=[])
    finally:
        await client.aclose()


def test_visible_text_strips_think_block() -> None:
    assert visible_text("<think>planning...</think>the answer") == "the answer"


def test_visible_text_handles_missing_opening_tag() -> None:
    # Some templates put <think> in the prompt, so the model's output only has the closer.
    assert visible_text("planning...</think>the answer") == "the answer"


def test_visible_text_passthrough_when_no_think_block() -> None:
    assert visible_text("just an answer") == "just an answer"


def test_visible_text_handles_none() -> None:
    assert visible_text(None) == ""
