from database.memories import save_human_feedback
from database.schemas.investigation import Evidence, Investigation


class FakeCollection:
    def __init__(self):
        self.document = None

    def insert_many(self, documents):
        self.document = documents[0]


class FakeDatabase:
    def __init__(self):
        self.memories = FakeCollection()


def test_human_feedback_is_embedded_with_provenance(monkeypatch):
    fake_database = FakeDatabase()
    monkeypatch.setattr("database.memories.database", lambda: fake_database)
    monkeypatch.setattr("database.memories.embed_texts", lambda texts: [[0.25] * 1536])
    investigation = Investigation(
        id="INV-123",
        incident_id="INC-123",
        observation="Payment provider returns 502s",
        scenario="payment_latency",
        status="completed",
        complete=True,
        evidence=[Evidence(id="EV-1", source="search_logs", summary="502 upstream")],
    )

    memory = save_human_feedback(investigation, "Check provider logs before deployment history.")
    saved = fake_database.memories.document

    assert memory.type.value == "human_feedback"
    assert saved["service"] == "payments"
    assert saved["provenance"]["investigation_id"] == "INV-123"
    assert saved["provenance"]["incident_id"] == "INC-123"
    assert saved["provenance"]["author"] == "human"
    assert saved["provenance"]["evidence_ids"] == ["EV-1"]
    assert saved["embedding_model"]
    assert len(saved["embedding"]) == 1536
