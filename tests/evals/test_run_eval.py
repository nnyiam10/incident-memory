from types import SimpleNamespace

from database.harness_versions import default_harness_version
from evals import run_eval


def diagnosis_for(scenario: str) -> str:
    return {
        "bad_deployment": "Deploy reduced the Redis pool configuration.",
        "redis_exhaustion": "Redis pool exhaustion caused checkout timeouts.",
        "payment_latency": "Payment provider latency caused upstream failures.",
    }[scenario]


def test_candidate_passes_when_accuracy_is_preserved_and_efficiency_improves(monkeypatch):
    active = default_harness_version()
    candidate = active.model_copy(update={"version": "v0.5.0", "status": "candidate"})

    def fake_investigate(_, __, scenario, harness):
        candidate_run = harness.version == "v0.5.0"
        return SimpleNamespace(diagnosis=diagnosis_for(scenario), actions=["a", "b"] if candidate_run else ["a", "b", "c"], duration_ms=80 if candidate_run else 100)

    monkeypatch.setattr(run_eval, "investigate", fake_investigate)
    result = run_eval.compare_harnesses(active, candidate)
    assert result.passed is True
    assert result.candidate.accuracy == 1
    assert result.candidate.total_actions < result.baseline.total_actions


def test_candidate_fails_when_any_diagnosis_is_wrong(monkeypatch):
    active = default_harness_version()
    candidate = active.model_copy(update={"version": "v0.5.0", "status": "candidate"})

    def fake_investigate(_, __, scenario, harness):
        diagnosis = "Unknown root cause" if harness.version == "v0.5.0" and scenario == "payment_latency" else diagnosis_for(scenario)
        return SimpleNamespace(diagnosis=diagnosis, actions=["a", "b"], duration_ms=80)

    monkeypatch.setattr(run_eval, "investigate", fake_investigate)
    result = run_eval.compare_harnesses(active, candidate)
    assert result.passed is False
    assert "accuracy" in result.reasons[0]
