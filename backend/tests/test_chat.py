import json

import pytest
from fastapi.testclient import TestClient

import chat_console.chat as chat_module
from chat_console.main import create_app


class FakeMcpClient:
    """Stands in for a real restaurant-mcp-server connection (PROJECT6_SCOPE.md section 8:
    backend tests mock the MCP client rather than needing a live server)."""

    last_call: tuple[str, dict] | None = None

    def __init__(self, server_url: str) -> None:
        self.server_url = server_url

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc_info):
        return None

    @property
    def instructions(self) -> str:
        return "FAKE SERVER INSTRUCTIONS"

    async def list_tools(self):
        return [
            {
                "name": "get_weather",
                "description": "Weather lookup",
                "input_schema": {"type": "object", "properties": {}},
            }
        ]

    async def call_tool(self, name: str, args: dict):
        FakeMcpClient.last_call = (name, args)
        return {"is_error": False, "text": "sunny, 22C"}


class OneToolThenAnswerLlm:
    """First step: calls get_weather. Second step: a long final answer (long enough to
    produce more than one word-chunk, so the chunking path is exercised too)."""

    def __init__(self, *args, **kwargs) -> None:
        self.step = 0

    async def aclose(self) -> None:
        return None

    async def complete(self, messages, tools):
        self.step += 1
        if self.step == 1:
            return {
                "choices": [
                    {
                        "message": {
                            "content": "",
                            "tool_calls": [
                                {
                                    "id": "call-1",
                                    "function": {"name": "get_weather", "arguments": "{}"},
                                }
                            ],
                        }
                    }
                ]
            }
        long_answer = "It is sunny and twenty two degrees today in the city you asked about."
        return {"choices": [{"message": {"content": long_answer}}]}


class ImmediateAnswerLlm:
    def __init__(self, *args, **kwargs) -> None:
        pass

    async def aclose(self) -> None:
        return None

    async def complete(self, messages, tools):
        return {"choices": [{"message": {"content": "hello there"}}]}


class ErroringMcpClient(FakeMcpClient):
    async def __aenter__(self):
        raise ConnectionError("mcp server unreachable")


def _events(response) -> list[tuple[str, dict]]:
    out: list[tuple[str, dict]] = []
    event = None
    for line in response.iter_lines():
        if line.startswith("event:"):
            event = line.split(":", 1)[1].strip()
        elif line.startswith("data:") and event:
            out.append((event, json.loads(line.split(":", 1)[1].strip())))
    return out


@pytest.fixture
def client(monkeypatch) -> TestClient:
    chat_module._HISTORY.clear()
    return TestClient(create_app())


def test_tool_call_then_answer(monkeypatch, client: TestClient) -> None:
    monkeypatch.setattr(chat_module, "McpClient", FakeMcpClient)
    monkeypatch.setattr(chat_module, "LlmClient", OneToolThenAnswerLlm)

    with client.stream(
        "POST", "/api/chat", json={"conversation_id": "c1", "message": "weather in Istanbul?"}
    ) as response:
        events = _events(response)

    names = [e for e, _ in events]
    assert names[:2] == ["tool_call", "tool_result"]
    assert names[-1] == "done"
    assert all(n == "token" for n in names[2:-1])
    assert ("tool_call", {"name": "get_weather", "args": {}}) in events
    tool_result = next(d for e, d in events if e == "tool_result")
    assert tool_result == {"name": "get_weather", "ok": True, "summary": "sunny, 22C"}

    full_answer = "".join(d["text"] for e, d in events if e == "token")
    assert full_answer.strip() == (
        "It is sunny and twenty two degrees today in the city you asked about."
    )
    assert FakeMcpClient.last_call == ("get_weather", {})

    # History keeps user + assistant turns (not tool-call bookkeeping).
    assert chat_module._HISTORY["c1"] == [
        {"role": "user", "content": "weather in Istanbul?"},
        {"role": "assistant", "content": full_answer.strip()},
    ]


def test_immediate_answer_without_tool_calls(monkeypatch, client: TestClient) -> None:
    monkeypatch.setattr(chat_module, "McpClient", FakeMcpClient)
    monkeypatch.setattr(chat_module, "LlmClient", ImmediateAnswerLlm)

    with client.stream(
        "POST", "/api/chat", json={"conversation_id": "c2", "message": "hi"}
    ) as response:
        events = _events(response)

    assert [e for e, _ in events] == ["token", "done"]
    assert events[0][1] == {"text": "hello there"}


def test_mcp_connection_error_is_reported_and_stream_still_ends(
    monkeypatch, client: TestClient
) -> None:
    monkeypatch.setattr(chat_module, "McpClient", ErroringMcpClient)
    monkeypatch.setattr(chat_module, "LlmClient", ImmediateAnswerLlm)

    with client.stream(
        "POST", "/api/chat", json={"conversation_id": "c3", "message": "hi"}
    ) as response:
        events = _events(response)

    assert events[-1][0] == "done"
    name, ok, summary = (
        events[0][1]["name"],
        events[0][1]["ok"],
        events[0][1]["summary"],
    )
    assert events[0][0] == "tool_result"
    assert name == "_system"
    assert ok is False
    assert "mcp server unreachable" in summary


def test_second_turn_reuses_history(monkeypatch, client: TestClient) -> None:
    monkeypatch.setattr(chat_module, "McpClient", FakeMcpClient)
    monkeypatch.setattr(chat_module, "LlmClient", ImmediateAnswerLlm)

    with client.stream("POST", "/api/chat", json={"conversation_id": "c4", "message": "first"}):
        pass
    with client.stream("POST", "/api/chat", json={"conversation_id": "c4", "message": "second"}):
        pass

    contents = [m["content"] for m in chat_module._HISTORY["c4"]]
    assert contents == ["first", "hello there", "second", "hello there"]
