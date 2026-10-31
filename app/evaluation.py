
from app.incident_report import IncidentReport


def evaluate_report(
    expected_diagnosis: str,
    report: IncidentReport,
    tool_trace: list[dict],
) -> dict:
    """
    Compare an agent's report against the known diagnosis.

    This evaluates correctness, not the quality of every explanation.
    """

    diagnosis_correct = report.diagnosis == expected_diagnosis

    return {
        "expected_diagnosis": expected_diagnosis,
        "actual_diagnosis": report.diagnosis,
        "diagnosis_correct": diagnosis_correct,
        "tool_calls": len(tool_trace),
        "evidence_count": len(report.evidence),
        "hypothesis_count": len(report.hypotheses),
        "confidence": report.confidence,
    }
