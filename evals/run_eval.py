from uuid import uuid4

from agent.harness.runner import investigate
from database.schemas.evaluation import EvaluationCaseResult, HarnessEvaluation, VersionEvaluationMetrics
from database.schemas.harness_version import HarnessVersion

CASES = [
    ("bad_deployment", "Checkout requests started timing out immediately after the latest deployment.", ["redis", "pool", "deploy"]),
    ("redis_exhaustion", "Checkout has Redis connection exhaustion and pool-wait warnings.", ["redis", "pool"]),
    ("payment_latency", "The external payment provider is slow and checkout returns upstream 502 errors.", ["payment", "provider"]),
]

def evaluate_version(harness: HarnessVersion) -> VersionEvaluationMetrics:
    results = []
    for scenario, observation, expected_terms in CASES:
        state = investigate(f"EVAL-{uuid4().hex[:8]}", observation, scenario=scenario, harness=harness)
        diagnosis = state.diagnosis or ""
        normalized = diagnosis.lower()
        accurate = all(term in normalized for term in expected_terms)
        results.append(EvaluationCaseResult(scenario=scenario, observation=observation, expected_terms=expected_terms, diagnosis=diagnosis, accurate=accurate, action_count=len(state.actions), duration_ms=state.duration_ms))
    return VersionEvaluationMetrics(version=harness.version, accuracy=sum(item.accurate for item in results) / len(results), total_actions=sum(item.action_count for item in results), total_duration_ms=sum(item.duration_ms for item in results), cases=results)

def compare_harnesses(active: HarnessVersion, candidate: HarnessVersion) -> HarnessEvaluation:
    baseline = evaluate_version(active)
    proposed = evaluate_version(candidate)
    accuracy_preserved = proposed.accuracy == 1.0 and proposed.accuracy >= baseline.accuracy
    actions_not_worse = proposed.total_actions <= baseline.total_actions
    time_not_worse = proposed.total_duration_ms <= baseline.total_duration_ms
    efficiency_improved = proposed.total_actions < baseline.total_actions or proposed.total_duration_ms < baseline.total_duration_ms
    reasons = []
    if not accuracy_preserved: reasons.append("Candidate must preserve 100% diagnosis accuracy.")
    if not actions_not_worse: reasons.append("Candidate used more diagnostic actions.")
    if not time_not_worse: reasons.append("Candidate took longer to diagnose the scenarios.")
    if not efficiency_improved: reasons.append("Candidate did not improve action or time efficiency.")
    return HarnessEvaluation(id=f"EVAL-{uuid4().hex[:12]}", active_version=active.version, candidate_version=candidate.version, baseline=baseline, candidate=proposed, passed=not reasons, reasons=reasons)
