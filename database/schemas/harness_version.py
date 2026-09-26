from datetime import datetime, timezone
from typing import Literal
from pydantic import BaseModel, Field

class MemoryContextPolicy(BaseModel):
    types: list[str] = Field(default_factory=lambda: ["human_feedback", "procedural", "negative"])
    limit: int = 3
    minimum_score: float = 0.0
    baseline_feedback_only: bool = True

class HarnessVersion(BaseModel):
    version: str
    status: Literal["active", "candidate", "retired"] = "candidate"
    reasoning_model: str
    allowed_tools: list[str]
    tool_order_policy: str
    context_policy: MemoryContextPolicy
    minimum_evidence_without_memory: int = 3
    minimum_evidence_with_feedback: int = 2
    max_actions: int = 20
    parent_version: str | None = None
    created_by: str = "system"
    promoted_by: str | None = None
    evaluation_status: Literal["not_run", "running", "passed", "failed"] = "not_run"
    latest_evaluation_id: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    promoted_at: datetime | None = None
