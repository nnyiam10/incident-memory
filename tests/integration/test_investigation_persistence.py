from apps.api.routes import investigations
from database.schemas.investigation import Investigation
from database.schemas.memory import Memory, MemoryType, Provenance


class InsertResult:
    inserted_id = "mongo-id"


class FakeCollection:
    def __init__(self):
        self.document = None

    def insert_one(self, document):
        self.document = document
        return InsertResult()


class FakeDatabase:
    def __init__(self):
        self.investigations = FakeCollection()


def test_post_investigation_persists_actions(monkeypatch):
    fake_database = FakeDatabase()
    monkeypatch.setattr("database.investigations.database", lambda: fake_database)
    monkeypatch.setattr(
        "agent.harness.runner.choose_next_action",
        lambda *args: (_ for _ in ()).throw(RuntimeError("offline test")),
    )
    monkeypatch.setattr(investigations, "save_memories", lambda memories: memories)
    monkeypatch.setattr(investigations, "attach_consolidated_memories", lambda *args: None)

    response = investigations.start(
        investigations.StartRequest(
            incident_id="INC-TEST",
            observation="Checkout times out after deploy",
            scenario="bad_deployment",
        )
    )

    saved = fake_database.investigations.document
    assert response.investigation_id == saved["id"]
    assert saved["incident_id"] == "INC-TEST"
    assert saved["status"] == "completed"
    assert saved["complete"] is True
    assert saved["action_count"] == 3
    assert saved["actions"] == response.actions
    assert len(saved["hypotheses"]) >= 1
    assert len(saved["evidence"]) == 3
    assert saved["diagnosis"]
    assert len(saved["remediation"]) >= 1
    assert len(response.consolidated_memory_ids) >= 2
    assert saved["created_at"]
    assert saved["completed_at"]


def saved_investigation():
    return Investigation(
        id="INV-SAVED",
        incident_id="INC-SAVED",
        observation="Saved observation",
        scenario="bad_deployment",
        status="completed",
        actions=["query_metrics: {}"],
        action_count=1,
        complete=True,
    )


def test_list_investigations(monkeypatch):
    monkeypatch.setattr(investigations, "list_investigations", lambda limit: [saved_investigation()])
    result = investigations.list_saved(limit=1)
    assert result[0].id == "INV-SAVED"


def test_get_investigation(monkeypatch):
    monkeypatch.setattr(investigations, "get_investigation", lambda investigation_id: saved_investigation())
    result = investigations.get_saved("INV-SAVED")
    assert result.incident_id == "INC-SAVED"


def test_completed_investigation_accepts_human_correction(monkeypatch):
    investigation = saved_investigation()
    memory = Memory(
        id="INC-SAVED:feedback:1",
        type=MemoryType.HUMAN_FEEDBACK,
        title="Engineer correction",
        content="Provider failures surface as 502s.",
        service="payments",
        confidence=1,
        provenance=Provenance(incident_id="INC-SAVED", investigation_id="INV-SAVED", author="human"),
    )
    attached = {}
    monkeypatch.setattr(investigations, "get_investigation", lambda investigation_id: investigation)
    monkeypatch.setattr(investigations, "save_human_feedback", lambda *args: memory)
    monkeypatch.setattr(investigations, "attach_correction", lambda investigation_id, correction, memory_id: attached.update({"id": investigation_id, "correction": correction, "memory_id": memory_id}))

    response = investigations.add_correction(
        "INV-SAVED",
        investigations.CorrectionRequest(correction="Provider failures surface as 502s."),
    )

    assert response.memory_type == "human_feedback"
    assert response.indexed_by == "memory_vector"
    assert attached["memory_id"] == memory.id
