from apps.api.routes import investigations
from database.schemas.investigation import Investigation


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
    assert len(saved["hypotheses"]) == 3
    assert len(saved["evidence"]) == 3
    assert saved["diagnosis"]
    assert len(saved["remediation"]) == 3
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
