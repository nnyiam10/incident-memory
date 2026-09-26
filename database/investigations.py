from datetime import datetime, timezone
from uuid import uuid4

from agent.harness.state import InvestigationState
from database.mongodb import database
from database.schemas.investigation import Investigation


def save_investigation(state: InvestigationState, scenario: str) -> Investigation:
    now = datetime.now(timezone.utc)
    investigation = Investigation(
        id=f"INV-{uuid4().hex[:12]}",
        incident_id=state.incident_id,
        observation=state.observation,
        scenario=scenario,
        status="completed" if state.complete else "running",
        hypotheses=state.hypotheses,
        evidence=state.evidence,
        retrieved_memory_ids=[
            memory["id"] for memory in state.memories if memory.get("id")
        ],
        actions=state.actions,
        action_count=len(state.actions),
        correction=state.correction,
        complete=state.complete,
        created_at=now,
        completed_at=now if state.complete else None,
    )
    database().investigations.insert_one(investigation.model_dump(mode="json"))
    return investigation
