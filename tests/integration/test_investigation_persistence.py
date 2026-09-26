from apps.api.routes import investigations


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
    assert saved["created_at"]
    assert saved["completed_at"]
