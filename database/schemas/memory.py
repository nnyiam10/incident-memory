from datetime import datetime, timezone
from enum import StrEnum
from pydantic import BaseModel, Field

class MemoryType(StrEnum):
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"
    NEGATIVE = "negative"
    HUMAN_FEEDBACK = "human_feedback"

class Provenance(BaseModel):
    incident_id: str
    evidence_ids: list[str] = Field(default_factory=list)
    author: str = "agent"

class Memory(BaseModel):
    id: str
    type: MemoryType
    title: str
    content: str
    service: str | None = None
    confidence: float = Field(ge=0, le=1)
    provenance: Provenance
    usage_count: int = 0
    contradiction_ids: list[str] = Field(default_factory=list)
    supersedes: str | None = None
    status: str = "active"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

