from agent.harness.budget import Budget
from agent.harness.state import InvestigationState
from agent.policies.guardrails import authorize
from agent.tools.simulated import get_deployments, query_metrics, search_logs

def investigate(incident_id: str, observation: str, scenario: str = "bad_deployment", correction: str | None = None) -> InvestigationState:
    state = InvestigationState(incident_id=incident_id, observation=observation, correction=correction)
    budget = Budget()
    plan = ["get_deployments", "query_metrics", "search_logs"] if correction else ["query_metrics", "search_logs", "get_deployments"]
    for tool in plan:
        if not budget.allows(len(state.actions)): break
        authorize(tool, "sandbox")
        result = {"get_deployments": get_deployments, "query_metrics": query_metrics, "search_logs": search_logs}[tool](scenario)
        state.actions.append(f"{tool}: {str(result)[:180]}")
    state.complete = True
    return state

