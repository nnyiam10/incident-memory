from datetime import datetime, timezone
from pydantic import BaseModel, Field

class Evidence(BaseModel):
    id: str
    source: str
    summary: str
    supports: list[str] = Field(default_factory=list)
    contradicts: list[str] = Field(default_factory=list)

class Hypothesis(BaseModel):
    id: str
    statement: str
    confidence: float = Field(ge=0, le=1)
    status: str = "open"
    evidence_ids: list[str] = Field(default_factory=list)

class Investigation(BaseModel):
    id: str
    incident_id: str
    status: str = "queued"
    hypotheses: list[Hypothesis] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)
    retrieved_memory_ids: list[str] = Field(default_factory=list)
    action_count: int = 0
    diagnosis: str | None = None
    remediation: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

