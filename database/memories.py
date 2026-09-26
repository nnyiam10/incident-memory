from uuid import uuid4

from agent.policies.models import EMBEDDING_MODEL
from database.embeddings import embed_texts, memory_text
from database.mongodb import database
from database.schemas.investigation import Investigation
from database.schemas.memory import Memory, MemoryType, Provenance


def service_for_investigation(investigation: Investigation) -> str:
    return "payments" if investigation.scenario == "payment_latency" else "checkout"


def save_human_feedback(investigation: Investigation, correction: str, author: str = "human") -> Memory:
    memory = Memory(
        id=f"{investigation.incident_id}:feedback:{uuid4().hex[:10]}",
        type=MemoryType.HUMAN_FEEDBACK,
        title="Engineer correction",
        content=correction,
        service=service_for_investigation(investigation),
        confidence=1.0,
        provenance=Provenance(
            incident_id=investigation.incident_id,
            investigation_id=investigation.id,
            evidence_ids=[item.id for item in investigation.evidence],
            author=author,
        ),
    )
    document = memory.model_dump(mode="json")
    document["embedding"] = embed_texts([memory_text(document)])[0]
    document["embedding_model"] = EMBEDDING_MODEL
    database().memories.insert_one(document)
    return memory
