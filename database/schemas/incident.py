from datetime import datetime, timezone
from pydantic import BaseModel, Field

class Incident(BaseModel):
    id: str
    title: str
    description: str
    service: str
    severity: str = "SEV-2"
    symptoms: list[str] = Field(default_factory=list)
    status: str = "open"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

