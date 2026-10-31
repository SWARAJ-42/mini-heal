
from app import config
from app.incident_report import (
    IncidentEvidence,
    IncidentReport,
)
from scripts.diagnose import diagnose


def investigate(evidence: IncidentEvidence) -> IncidentReport:
    health = {
        "reachable": evidence.health_reachable,
        "http_status": evidence.health_http_status,
        "body": evidence.health_body,
    }

    diagnosis = diagnose(
        evidence.container_status,
        health,
    )

    if diagnosis == "HEALTHY":
        summary = f"{config.APP_NAME} is healthy."
        hypotheses = []
        actions = ["Continue monitoring service health."]
        confidence = "high"

    elif diagnosis == "CONTAINER_NOT_RUNNING":
        summary = f"The {config.APP_NAME} container is not running."
        hypotheses = [
            "The container may have stopped or exited unexpectedly."
        ]
        actions = [
            "Inspect the container exit status and recent logs.",
            "Determine the cause before restarting the service.",
        ]
        confidence = "high"

    elif diagnosis == "SERVICE_UNREACHABLE":
        summary = "The API is unreachable while the container is running."
        hypotheses = [
            "The application may have crashed or stopped accepting connections.",
            "The port mapping or application startup may be incorrect.",
        ]
        actions = [
            "Inspect recent container logs.",
            "Check the application process and port mapping.",
        ]
        confidence = "medium"

    elif diagnosis == "HEALTH_CHECK_FAILED":
        summary = "The health endpoint is reporting a failure."
        hypotheses = [
            "A dependency may be unavailable.",
            "The health endpoint may have encountered an internal error.",
        ]
        actions = [
            "Inspect the health response and recent application logs.",
            "Verify the dependency before attempting remediation.",
        ]
        confidence = "medium"

    else:
        diagnosis = "UNKNOWN"
        summary = "The evidence is insufficient for a reliable diagnosis."
        hypotheses = ["The available signals may be incomplete."]
        actions = ["Collect additional logs and health information."]
        confidence = "low"

    return IncidentReport(
        diagnosis=diagnosis,
        summary=summary,
        evidence=[
            f"Container status: {evidence.container_status}",
            f"Health endpoint reachable: {evidence.health_reachable}",
            f"Health HTTP status: {evidence.health_http_status}",
            f"Health response body: {evidence.health_body}",
        ],
        hypotheses=hypotheses,
        recommended_actions=actions,
        confidence=confidence,
    )
