from agent.harness.planner import PlannerDecision, PlannedHypothesis
from agent.harness.runner import infer_scenario, investigate

def scripted_planner(actions):
    sequence = iter(actions)
    def choose(*args):
        evidence_ids = [item["id"] for item in args[1]]
        action = next(sequence, None)
        return PlannerDecision(action=action, rationale="test", hypotheses=[PlannedHypothesis(statement="Evidence-backed cause", confidence=.9, status="confirmed", evidence_ids=evidence_ids)] if evidence_ids else [], sufficient_evidence=action is None, diagnosis="Evidence-backed test diagnosis" if action is None else None, remediation=["Test remediation"] if action is None else [])
    return choose

def test_model_planner_controls_investigation_order(monkeypatch):
    monkeypatch.setattr("agent.harness.runner.choose_next_action", scripted_planner(["search_logs", "query_metrics", None]))
    result = investigate("INC-1", "upstream 502 errors", scenario="payment_latency", correction="Check logs before deployment history")
    assert [action.split(":", 1)[0] for action in result.actions] == ["search_logs", "query_metrics"]
    assert result.diagnosis == "Evidence-backed test diagnosis"

def test_retrieved_correction_reduces_required_actions(monkeypatch):
    monkeypatch.setattr("agent.harness.runner.choose_next_action", scripted_planner(["query_metrics", "search_logs", "get_deployments", None]))
    first = investigate("INC-FIRST", "checkout timeouts", scenario="bad_deployment")
    monkeypatch.setattr("agent.harness.runner.choose_next_action", scripted_planner(["query_metrics", "search_logs", None]))
    second = investigate("INC-SECOND", "related checkout timeouts", scenario="bad_deployment", correction="Skip deployment history after pool-wait evidence", baseline_investigation_id="INV-FIRST")
    assert len(first.actions) == 3
    assert len(second.actions) == 2
    assert second.baseline_investigation_id == "INV-FIRST"

def test_incident_description_selects_different_simulated_evidence():
    assert infer_scenario("Payment provider returns 502 upstream errors") == "payment_latency"
    assert infer_scenario("Redis connection pool is exhausted") == "redis_exhaustion"
    assert infer_scenario("Pool-wait warnings with no 502 responses") == "redis_exhaustion"
    assert infer_scenario("Timeouts began after latest deploy") == "bad_deployment"

def test_repeated_model_action_is_rejected(monkeypatch):
    monkeypatch.setattr("agent.harness.runner.choose_next_action", scripted_planner(["query_metrics", "query_metrics"]))
    try:
        investigate("INC-2", "timeouts")
    except PermissionError as error:
        assert "unavailable action" in str(error)
    else:
        raise AssertionError("Repeated action should be rejected")
