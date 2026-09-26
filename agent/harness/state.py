from pydantic import BaseModel, Field
from database.schemas.investigation import Evidence, Hypothesis

class InvestigationState(BaseModel):
    investigation_id: str | None = None
    incident_id: str
    observation: str
    hypotheses: list[Hypothesis] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)
    memories: list[dict] = Field(default_factory=list)
    actions: list[str] = Field(default_factory=list)
    correction: str | None = None
    complete: bool = False
    diagnosis: str | None = None
    remediation: list[str] = Field(default_factory=list)
