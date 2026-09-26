from datetime import datetime, timezone
from pydantic import BaseModel, Field

class EvaluationCaseResult(BaseModel):
    scenario: str
    observation: str
    expected_terms: list[str]
    diagnosis: str
    accurate: bool
    action_count: int
    duration_ms: int

class VersionEvaluationMetrics(BaseModel):
    version: str
    accuracy: float
    total_actions: int
    total_duration_ms: int
    cases: list[EvaluationCaseResult]

class HarnessEvaluation(BaseModel):
    id: str
    active_version: str
    candidate_version: str
    baseline: VersionEvaluationMetrics
    candidate: VersionEvaluationMetrics
    passed: bool
    reasons: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
