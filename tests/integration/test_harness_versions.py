import pytest
from fastapi import HTTPException

from apps.api.routes import harnesses
from database.harness_versions import default_harness_version


def candidate_request():
    active = default_harness_version()
    return harnesses.CreateHarnessRequest(
        version="v0.5.0",
        reasoning_model=active.reasoning_model,
        allowed_tools=active.allowed_tools,
        tool_order_policy="memory_guided_first",
        context_policy=active.context_policy,
        minimum_evidence_without_memory=3,
        minimum_evidence_with_feedback=1,
        max_actions=15,
        parent_version=active.version,
    )


def test_create_candidate_is_never_active(monkeypatch):
    captured = {}
    monkeypatch.setattr(harnesses, "create_harness_candidate", lambda candidate: captured.setdefault("candidate", candidate))
    response = harnesses.create(candidate_request())
    assert response.status == "candidate"
    assert response.parent_version == "v0.4.0"
    assert captured["candidate"].tool_order_policy == "memory_guided_first"


def test_promotion_requires_explicit_confirmation():
    with pytest.raises(HTTPException) as error:
        harnesses.promote("v0.5.0", harnesses.PromoteRequest(confirmed=False))
    assert error.value.status_code == 422


def test_confirmed_promotion_is_audited(monkeypatch):
    promoted = default_harness_version().model_copy(update={"version": "v0.5.0", "status": "active", "promoted_by": "human"})
    monkeypatch.setattr(harnesses, "promote_harness_version", lambda version, approved_by: promoted)
    response = harnesses.promote("v0.5.0", harnesses.PromoteRequest(confirmed=True, approved_by="human"))
    assert response.status == "active"
    assert response.promoted_by == "human"
