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
        scenario=state.scenario if state.scenario != "auto" else scenario,
        status="completed" if state.complete else "running",
        hypotheses=state.hypotheses,
        evidence=state.evidence,
        retrieved_memory_ids=[
            memory["id"] for memory in state.memories if memory.get("id")
        ],
        baseline_investigation_id=state.baseline_investigation_id,
        actions=state.actions,
        action_count=len(state.actions),
        correction=state.correction,
        complete=state.complete,
        diagnosis=state.diagnosis,
        remediation=state.remediation,
        reasoning_provider=state.reasoning_provider,
        reasoning_model=state.reasoning_model,
        duration_ms=state.duration_ms,
        dead_end_count=state.dead_end_count,
        harness_version=state.harness_version,
        harness_config=state.harness_config,
        created_at=now,
        completed_at=now if state.complete else None,
    )
    database().investigations.insert_one(investigation.model_dump(mode="json"))
    return investigation


def get_investigation(investigation_id: str) -> Investigation | None:
    document = database().investigations.find_one({"id": investigation_id})
    if not document:
        return None
    document.pop("_id", None)
    return Investigation.model_validate(document)


def list_investigations(limit: int = 20) -> list[Investigation]:
    cursor = database().investigations.find().sort("created_at", -1).limit(limit)
    investigations = []
    for document in cursor:
        document.pop("_id", None)
        investigations.append(Investigation.model_validate(document))
    return investigations


def attach_correction(investigation_id: str, correction: str, memory_id: str) -> Investigation | None:
    database().investigations.update_one(
        {"id": investigation_id},
        {
            "$set": {"correction": correction},
            "$addToSet": {"correction_memory_ids": memory_id},
        },
    )
    return get_investigation(investigation_id)


def attach_consolidated_memories(investigation_id: str, memory_ids: list[str]) -> Investigation | None:
    database().investigations.update_one(
        {"id": investigation_id},
        {"$set": {"consolidated_memory_ids": memory_ids}},
    )
    return get_investigation(investigation_id)
