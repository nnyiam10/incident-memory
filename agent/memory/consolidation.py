from database.schemas.memory import Memory, MemoryType, Provenance
from database.schemas.investigation import Investigation

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


def consolidate_investigation(investigation: Investigation) -> list[Memory]:
    service = "payments" if investigation.scenario == "payment_latency" else "checkout"
    all_evidence_ids = [item.id for item in investigation.evidence]
    provenance = Provenance(
        incident_id=investigation.incident_id,
        investigation_id=investigation.id,
        harness_version=investigation.harness_version,
        evidence_ids=all_evidence_ids,
    )
    remediation = " ".join(investigation.remediation) or "No remediation was proposed."
    action_path = " → ".join(action.split(":", 1)[0] for action in investigation.actions)
    memories = [
        Memory(
            id=f"{investigation.incident_id}:episode:{investigation.id}",
            type=MemoryType.EPISODIC,
            title=f"Outcome of {investigation.incident_id}",
            content=f"Symptoms: {investigation.observation}. Root cause: {investigation.diagnosis}. Proposed remediation: {remediation}",
            service=service,
            confidence=max((item.confidence for item in investigation.hypotheses), default=.75),
            provenance=provenance,
        ),
        Memory(
            id=f"{investigation.incident_id}:procedure:{investigation.id}",
            type=MemoryType.PROCEDURAL,
            title=f"Investigation path for {service}",
            content=f"Diagnostic sequence: {action_path}. This path reached: {investigation.diagnosis}",
            service=service,
            confidence=.82,
            provenance=provenance,
        ),
    ]
    evidence_by_id = {item.id: item.summary for item in investigation.evidence}
    rejected = [item for item in investigation.hypotheses if item.status == "ruled_out" or (item.status != "confirmed" and item.confidence <= .25)]
    for index, hypothesis in enumerate(rejected):
        evidence_ids = hypothesis.evidence_ids or all_evidence_ids
        evidence = " ".join(evidence_by_id[item] for item in evidence_ids if item in evidence_by_id)
        memories.append(
            Memory(
                id=f"{investigation.incident_id}:negative:{investigation.id}:{index}",
                type=MemoryType.NEGATIVE,
                title=f"Ruled out: {hypothesis.statement}",
                content=evidence or "The available incident evidence did not support this hypothesis.",
                service=service,
                confidence=max(.75, 1 - hypothesis.confidence),
                provenance=Provenance(
                    incident_id=investigation.incident_id,
                    investigation_id=investigation.id,
                    harness_version=investigation.harness_version,
                    evidence_ids=evidence_ids,
                ),
            )
        )
    return memories
