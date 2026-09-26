from database.schemas.memory import Memory, MemoryType, Provenance

def consolidate(incident_id: str, root_cause: str, fix: str, failed: list[dict], feedback: str | None = None) -> list[Memory]:
    memories = [
        Memory(id=f"{incident_id}:episode", type=MemoryType.EPISODIC, title=f"Outcome of {incident_id}", content=f"Root cause: {root_cause}. Successful fix: {fix}.", confidence=.95, provenance=Provenance(incident_id=incident_id)),
        Memory(id=f"{incident_id}:procedure", type=MemoryType.PROCEDURAL, title="Reusable investigation path", content="Check dependency-level latency and deployment configuration before external status pages.", confidence=.82, provenance=Provenance(incident_id=incident_id)),
    ]
    memories.extend(Memory(id=f"{incident_id}:negative:{i}", type=MemoryType.NEGATIVE, title=f"Ruled out: {item['hypothesis']}", content=item['evidence'], confidence=.9, provenance=Provenance(incident_id=incident_id)) for i,item in enumerate(failed))
    if feedback:
        memories.append(Memory(id=f"{incident_id}:feedback", type=MemoryType.HUMAN_FEEDBACK, title="Engineer correction", content=feedback, confidence=1, provenance=Provenance(incident_id=incident_id, author="human")))
    return memories

def supersede(old: Memory, new: Memory) -> tuple[Memory, Memory]:
    old.status = "superseded"
    old.contradiction_ids.append(new.id)
    new.supersedes = old.id
    new.contradiction_ids.append(old.id)
    return old, new

