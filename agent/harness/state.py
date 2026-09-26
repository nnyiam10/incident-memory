from pydantic import BaseModel, Field
from database.schemas.investigation import Evidence, Hypothesis

class InvestigationState(BaseModel):
    investigation_id: str | None = None
    incident_id: str
    observation: str
    scenario: str = "auto"
    hypotheses: list[Hypothesis] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)
    memories: list[dict] = Field(default_factory=list)
    consolidated_memory_ids: list[str] = Field(default_factory=list)
    baseline_investigation_id: str | None = None
    actions: list[str] = Field(default_factory=list)
    correction: str | None = None
    complete: bool = False
    diagnosis: str | None = None
    remediation: list[str] = Field(default_factory=list)
    reasoning_provider: str = "openrouter"
    reasoning_model: str | None = None
    duration_ms: int = 0
    dead_end_count: int = 0
    harness_version: str = "unversioned"
    harness_config: dict = Field(default_factory=dict)
