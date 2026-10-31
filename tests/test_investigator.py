
from app.incident_report import IncidentEvidence
from app.investigator import investigate


def test_investigator_reports_healthy_service():
    evidence = IncidentEvidence(
        container_status="running",
        health_reachable=True,
        health_http_status=200,
        health_body={"status": "ok", "database": "ok"},
    )

    report = investigate(evidence)

    assert report.diagnosis == "HEALTHY"
    assert report.confidence == "high"
    assert report.hypotheses == []


def test_investigator_reports_stopped_container():
    evidence = IncidentEvidence(
        container_status="exited",
        health_reachable=False,
        health_http_status=None,
        health_body={},
    )

    report = investigate(evidence)

    assert report.diagnosis == "CONTAINER_NOT_RUNNING"
    assert report.confidence == "high"
    assert any(
        "logs" in action.lower()
        for action in report.recommended_actions
    )
