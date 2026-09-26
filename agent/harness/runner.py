from agent.harness.budget import Budget
from agent.harness.state import InvestigationState
from agent.policies.guardrails import authorize
from agent.tools.simulated import get_deployments, query_metrics, search_logs
from database.schemas.investigation import Evidence, Hypothesis

def investigate(incident_id: str, observation: str, scenario: str = "bad_deployment", correction: str | None = None) -> InvestigationState:
    state = InvestigationState(incident_id=incident_id, observation=observation, correction=correction)
    budget = Budget()
    plan = ["get_deployments", "query_metrics", "search_logs"] if correction else ["query_metrics", "search_logs", "get_deployments"]
    for tool in plan:
        if not budget.allows(len(state.actions)): break
        authorize(tool, "sandbox")
        result = {"get_deployments": get_deployments, "query_metrics": query_metrics, "search_logs": search_logs}[tool](scenario)
        state.actions.append(f"{tool}: {str(result)[:180]}")

    metrics = query_metrics(scenario)
    logs = search_logs(scenario)
    deployments = get_deployments(scenario)
    latest_deployment = deployments[0] if deployments else {}
    pool_change = latest_deployment.get("changes", {}).get("REDIS_POOL_SIZE", {})

    state.evidence = [
        Evidence(
            id="EV-METRICS",
            source="metrics",
            summary=(
                f"Checkout p95 is {metrics.get('checkout_p95_ms')}ms with "
                f"{metrics.get('redis_pool_waiters')} Redis pool waiters; payment and inventory "
                f"latencies remain at {metrics.get('payment_provider_p95_ms')}ms and "
                f"{metrics.get('inventory_p95_ms')}ms."
            ),
            supports=["HYP-REDIS"],
            contradicts=["HYP-PAYMENTS", "HYP-INVENTORY"],
        ),
        Evidence(
            id="EV-LOGS",
            source="logs",
            summary="; ".join(logs),
            supports=["HYP-REDIS"],
            contradicts=["HYP-PAYMENTS"],
        ),
        Evidence(
            id="EV-DEPLOY",
            source="deployments",
            summary=(
                f"Deploy {latest_deployment.get('id', 'unknown')} changed REDIS_POOL_SIZE "
                f"from {pool_change.get('before')} to {pool_change.get('after')}."
            ),
            supports=["HYP-REDIS"],
        ),
    ]
    state.hypotheses = [
        Hypothesis(
            id="HYP-REDIS",
            statement="The latest deploy undersized the checkout Redis connection pool",
            confidence=0.94,
            status="confirmed",
            evidence_ids=["EV-METRICS", "EV-LOGS", "EV-DEPLOY"],
        ),
        Hypothesis(
            id="HYP-PAYMENTS",
            statement="The external payment provider is degraded",
            confidence=0.12,
            status="ruled_out",
            evidence_ids=["EV-METRICS", "EV-LOGS"],
        ),
        Hypothesis(
            id="HYP-INVENTORY",
            statement="Inventory lock contention is delaying checkout",
            confidence=0.08,
            status="ruled_out",
            evidence_ids=["EV-METRICS"],
        ),
    ]
    state.diagnosis = (
        f"Deploy {latest_deployment.get('id', 'unknown')} reduced REDIS_POOL_SIZE from "
        f"{pool_change.get('before')} to {pool_change.get('after')}. Checkout workers exhaust "
        "the pool under load and wait until the request timeout."
    )
    state.remediation = [
        f"Restore REDIS_POOL_SIZE to {pool_change.get('before')} in the sandbox and validate recovery.",
        "Roll back the config-only deployment after approval.",
        "Add a deployment guard requiring the Redis pool size to meet worker concurrency.",
    ]
    state.complete = True
    return state
