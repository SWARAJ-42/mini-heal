
from typing import Literal

from pydantic import BaseModel, Field


class IncidentEvidence(BaseModel):
    container_status: str
    health_reachable: bool
    health_http_status: int | None
    health_body: dict
    recent_logs: list[str] = Field(default_factory=list)


class IncidentReport(BaseModel):
    diagnosis: Literal[
        "HEALTHY",
        "CONTAINER_NOT_RUNNING",
        "SERVICE_UNREACHABLE",
        "HEALTH_CHECK_FAILED",
        "UNKNOWN",
    ]

    summary: str
    evidence: list[str] = Field(default_factory=list)
    hypotheses: list[str] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)

    confidence: Literal["low", "medium", "high"]
