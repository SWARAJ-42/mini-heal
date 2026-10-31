
from types import SimpleNamespace

from app.ai_investigator import (
    investigate,
    execute_tool,
)
from app.incident_report import IncidentReport


def test_unknown_tool_is_rejected():
    result = execute_tool("run_shell_command", "{}")

    assert result["success"] is False
    assert "not allowed" in result["error"]


def test_tool_with_unexpected_arguments_is_rejected():
    result = execute_tool(
        "check_health",
        '{"url": "http://example.com"}',
    )

    assert result["success"] is False
    assert "does not accept arguments" in result["error"]


def test_invalid_json_is_rejected():
    result = execute_tool(
        "check_health",
        "not-json",
    )

    assert result["success"] is False
    assert "Invalid tool arguments" in result["error"]


def test_tool_call_loop(monkeypatch):
    # Replace the actual tool with a predictable fake.
    from app import ai_investigator

    monkeypatch.setitem(
        ai_investigator.AVAILABLE_TOOLS,
        "get_container_status",
        lambda: {
            "success": True,
            "status": "running",
        },
    )

    function_call = SimpleNamespace(
        type="function_call",
        name="get_container_status",
        arguments="{}",
        call_id="call_test_123",
    )

    first_response = SimpleNamespace(
        output=[function_call],
        output_text="",
        output_parsed=None,
    )

    final_report = IncidentReport(
        diagnosis="HEALTHY",
        summary="MiniHeal is running.",
        evidence=["Container status is running."],
        hypotheses=[],
        recommended_actions=[],
        confidence="high",
    )

    final_response = SimpleNamespace(
        output=[
            SimpleNamespace(type="message"),
        ],
        output_text="",
        output_parsed=final_report,
    )

    class FakeResponses:
        def __init__(self):
            self.calls = []
            self.responses = [
                first_response,
                final_response,
            ]

        def parse(self, **kwargs):
            self.calls.append(kwargs)
            return self.responses.pop(0)

    fake_responses = FakeResponses()

    fake_client = SimpleNamespace(
        responses=fake_responses,
    )

    result = investigate(client=fake_client)

    # Verify structured report.
    assert isinstance(result["report"], IncidentReport)
    assert result["report"].diagnosis == "HEALTHY"
    assert result["report"].summary == "MiniHeal is running."

    # Verify tool trace.
    assert len(result["tool_trace"]) == 1

    trace = result["tool_trace"][0]

    assert trace["sequence"] == 1
    assert trace["tool"] == "get_container_status"
    assert trace["success"] is True
    assert trace["result"]["status"] == "running"

    # Verify that the model received the tool result.
    assert len(fake_responses.calls) == 2

    second_input = fake_responses.calls[1]["input"]

    assert any(
        isinstance(item, dict)
        and item.get("type") == "function_call_output"
        and item.get("call_id") == "call_test_123"
        for item in second_input
    )
