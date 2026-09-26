from agent.memory.consolidation import consolidate
from agent.memory.consolidation import consolidate_investigation
from database.schemas.investigation import Evidence, Hypothesis, Investigation

def test_feedback_is_durable_memory():
    result = consolidate("INC-1", "root", "fix", [], "check deploys first")
    assert result[-1].type == "human_feedback"
    assert result[-1].provenance.author == "human"


def test_completed_investigation_becomes_typed_memories():
    investigation = Investigation(
        id="INV-1",
        incident_id="INC-1",
        observation="Checkout returns 502s",
        scenario="payment_latency",
        status="completed",
        complete=True,
        diagnosis="Payment provider latency",
        remediation=["Use the approved fallback."],
        actions=["search_logs: result", "query_metrics: result"],
        evidence=[Evidence(id="EV-1", source="logs", summary="502 upstream")],
        hypotheses=[
            Hypothesis(id="HYP-1", statement="Provider degraded", confidence=.94, status="confirmed", evidence_ids=["EV-1"]),
            Hypothesis(id="HYP-2", statement="Recent deploy", confidence=.12, status="open", evidence_ids=["EV-1"]),
        ],
    )

    memories = consolidate_investigation(investigation)
    assert [memory.type.value for memory in memories] == ["episodic", "procedural", "negative"]
    assert all(memory.service == "payments" for memory in memories)
    assert all(memory.provenance.investigation_id == "INV-1" for memory in memories)
    assert memories[-1].provenance.evidence_ids == ["EV-1"]
