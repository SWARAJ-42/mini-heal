
import pytest
from pydantic import ValidationError

from app.incident_report import (
    IncidentEvidence,
    IncidentReport,
)


def test_incident_evidence_defaults_to_no_logs():
    evidence = IncidentEvidence(
        container_status="running",
        health_reachable=True,
        health_http_status=200,
        health_body={"status": "ok", "database": "ok"},
    )

    assert evidence.recent_logs == []


def test_valid_incident_report():
    report = IncidentReport(
        diagnosis="HEALTH_CHECK_FAILED",
        summary="The health endpoint is reporting a failure.",
        evidence=["Health endpoint returned HTTP 503."],
        hypotheses=["A dependency may be unavailable."],
        recommended_actions=["Inspect recent application logs."],
        confidence="medium",
    )

    assert report.diagnosis == "HEALTH_CHECK_FAILED"
    assert report.confidence == "medium"


def test_invalid_diagnosis_is_rejected():
    with pytest.raises(ValidationError):
        IncidentReport(
            diagnosis="MAGIC_FIX",
            summary="Unknown diagnosis.",
            evidence=[],
            hypotheses=[],
            recommended_actions=[],
            confidence="low",
        )
