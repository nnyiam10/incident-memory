from agent.harness.budget import Budget
from agent.harness.planner import PlannerDecision, choose_next_action
from agent.harness.state import InvestigationState
from agent.policies.guardrails import authorize
from agent.policies.models import REASONING_MODEL
from agent.tools.simulated import get_deployments, query_metrics, search_logs
from database.schemas.investigation import Evidence, Hypothesis

EXECUTABLE_TOOLS = {"get_deployments": get_deployments, "query_metrics": query_metrics, "search_logs": search_logs}

def infer_scenario(observation: str) -> str:
    text = observation.lower()
    if any(term in text for term in ("payment", "provider", "502", "upstream")):
        return "payment_latency"
    if any(term in text for term in ("redis", "connection", "pool exhausted", "leak")) and "deploy" not in text:
        return "redis_exhaustion"
    return "bad_deployment"

def _fallback_decision(observation: str, remaining: list[str]) -> PlannerDecision:
    text = observation.lower()
    preference = (["search_logs", "query_metrics", "get_deployments"] if any(term in text for term in ("502", "error", "log")) else ["get_deployments", "query_metrics", "search_logs"] if any(term in text for term in ("deploy", "release", "config")) else ["query_metrics", "search_logs", "get_deployments"])
    action = next((name for name in preference if name in remaining), None)
    return PlannerDecision(action=action, rationale="Safe deterministic fallback", hypotheses=[], sufficient_evidence=action is None, diagnosis=None, remediation=[])

def _fallback_conclusion(scenario: str, evidence_ids: list[str]) -> tuple[list[Hypothesis], str, list[str]]:
    if scenario == "payment_latency":
        return [Hypothesis(id="HYP-1", statement="The external payment provider is degraded", confidence=.96, status="confirmed", evidence_ids=evidence_ids)], "The external payment provider is slow and returning upstream failures, causing checkout timeouts.", ["Validate the approved provider fallback in the sandbox and escalate with the latency and 502 evidence."]
    if scenario == "redis_exhaustion":
        return [Hypothesis(id="HYP-1", statement="Checkout is exhausting its Redis connections", confidence=.95, status="confirmed", evidence_ids=evidence_ids)], "Checkout reached its Redis client limit, exhausting the connection pool and delaying requests.", ["Validate connection cleanup in the sandbox and propose a bounded pool or client-lifecycle fix."]
    return [Hypothesis(id="HYP-1", statement="The latest deploy undersized the checkout Redis connection pool", confidence=.94, status="confirmed", evidence_ids=evidence_ids)], "The latest deployment reduced the Redis pool from 40 to 8, so checkout exhausts it under load.", ["Restore the prior pool size in the sandbox, validate recovery, then propose rollback and a deployment guard."]

def investigate(incident_id: str, observation: str, scenario: str = "auto", correction: str | None = None) -> InvestigationState:
    resolved_scenario = infer_scenario(observation) if scenario == "auto" else scenario
    state = InvestigationState(incident_id=incident_id, observation=observation, correction=correction, reasoning_model=REASONING_MODEL)
    budget, completed_tools, last_decision, planner_failed = Budget(), [], None, False

    while budget.allows(len(state.actions)):
        remaining = [name for name in EXECUTABLE_TOOLS if name not in completed_tools]
        evidence_payload = [item.model_dump() for item in state.evidence]
        try:
            decision = choose_next_action(observation, evidence_payload, completed_tools, remaining, correction)
        except Exception:
            planner_failed = True
            decision = _fallback_decision(observation, remaining)
        last_decision = decision
        if decision.sufficient_evidence and len(state.evidence) >= 2:
            break
        if decision.action is None:
            decision = _fallback_decision(observation, remaining)
        action = decision.action
        if action is None:
            break
        if action not in remaining or action not in EXECUTABLE_TOOLS:
            raise PermissionError(f"Planner requested unavailable action: {action}")
        authorize(action, "sandbox")
        result = EXECUTABLE_TOOLS[action](resolved_scenario)
        completed_tools.append(action)
        state.actions.append(f"{action}: {str(result)[:180]}")
        state.evidence.append(Evidence(id=f"EV-{len(state.evidence) + 1}", source=action, summary=str(result)))

    if last_decision and last_decision.hypotheses and last_decision.diagnosis:
        state.hypotheses = [Hypothesis(id=f"HYP-{index + 1}", **item.model_dump()) for index, item in enumerate(last_decision.hypotheses)]
        state.diagnosis, state.remediation = last_decision.diagnosis, last_decision.remediation
    else:
        state.hypotheses, state.diagnosis, state.remediation = _fallback_conclusion(resolved_scenario, [item.id for item in state.evidence])
    if planner_failed:
        state.reasoning_provider = "deterministic_fallback"
    state.complete = True
    return state
