import json

from app.incident_report import IncidentEvidence
from app.investigator import investigate
from scripts.diagnose import (
    get_container_status,
    get_health,
)


def main():
    health = get_health()

    evidence = IncidentEvidence(
        container_status=get_container_status(),
        health_reachable=health["reachable"],
        health_http_status=health["http_status"],
        health_body=health["body"],
    )

    report = investigate(evidence)

    print(json.dumps(report.model_dump(), indent=2))


if __name__ == "__main__":
    main()