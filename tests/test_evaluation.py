
from app.evaluation import evaluate_report
from app.incident_report import IncidentReport


def test_correct_diagnosis():
    report = IncidentReport(
        diagnosis="HEALTHY",
        summary="MiniHeal is healthy.",
        evidence=["Container is running.", "Health check returned HTTP 200."],
        hypotheses=[],
        recommended_actions=[],
        confidence="high",
    )

    tool_trace = [
        {"tool": "get_container_status"},
        {"tool": "check_health"},
    ]

    result = evaluate_report(
        expected_diagnosis="HEALTHY",
        report=report,
        tool_trace=tool_trace,
    )

    assert result["diagnosis_correct"] is True
    assert result["tool_calls"] == 2
    assert result["evidence_count"] == 2


def test_incorrect_diagnosis():
    report = IncidentReport(
        diagnosis="HEALTHY",
        summary="MiniHeal is healthy.",
        evidence=["Container is running."],
        hypotheses=[],
        recommended_actions=[],
        confidence="high",
    )

    result = evaluate_report(
        expected_diagnosis="HEALTH_CHECK_FAILED",
        report=report,
        tool_trace=[],
    )

    assert result["diagnosis_correct"] is False
    assert result["expected_diagnosis"] == "HEALTH_CHECK_FAILED"
    assert result["actual_diagnosis"] == "HEALTHY"
