
import json

from app.ai_investigator import investigate_with_ai
from app.incident_report import IncidentEvidence


evidence = IncidentEvidence(
    container_status="running",
    health_reachable=True,
    health_http_status=503,
    health_body={
        "status": "unhealthy",
        "database": "unavailable",
    },
    recent_logs=[
        "Health check failed: database unavailable",
        "Simulated database connectivity failure",
    ],
)

report = investigate_with_ai(evidence)

print(json.dumps(report.model_dump(), indent=2))
