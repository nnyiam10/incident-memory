import json
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from agent.policies.models import REASONING_MODEL, model_client

DiagnosticAction = Literal["query_metrics", "search_logs", "get_deployments"]

class PlannedHypothesis(BaseModel):
    model_config = ConfigDict(extra="forbid")
    statement: str
    confidence: float = Field(ge=0, le=1)
    status: Literal["open", "confirmed", "ruled_out"]
    evidence_ids: list[str]

class PlannerDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action: DiagnosticAction | None
    rationale: str
    hypotheses: list[PlannedHypothesis]
    sufficient_evidence: bool
    diagnosis: str | None
    remediation: list[str]

SYSTEM_PROMPT = """You are the read-only planner for Incident Memory.
Choose exactly one next diagnostic action, or finish when gathered evidence supports a diagnosis.
Use only actions supplied by the harness. Prefer the cheapest action that separates leading hypotheses.
On the first turn, follow the supplied triage hint; it encodes the symptom-specific discriminator.
Never invent results. Conclusions must cite supplied evidence IDs. Require two independent evidence sources.
Production changes are forbidden; remediation is advice only."""

def choose_next_action(observation: str, evidence: list[dict], completed_actions: list[str], allowed_actions: list[str], correction: str | None = None) -> PlannerDecision:
    text = observation.lower()
    triage_hint = (
        "Start with search_logs because explicit 502 or upstream errors are the strongest discriminator."
        if any(term in text for term in ("502", "upstream", "error"))
        else "Start with get_deployments because the symptom is explicitly correlated with a deploy or configuration change."
        if any(term in text for term in ("deploy", "release", "config"))
        else "Start with query_metrics to identify which dependency or resource is saturated."
    )
    payload = {"incident_observation": observation, "human_correction": correction, "triage_hint": triage_hint, "allowed_actions": allowed_actions, "completed_actions": completed_actions, "evidence": evidence}
    completion = model_client().chat.completions.create(
        model=REASONING_MODEL,
        messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": json.dumps(payload)}],
        response_format={"type": "json_schema", "json_schema": {"name": "investigation_planner_decision", "strict": True, "schema": PlannerDecision.model_json_schema()}},
        extra_body={"provider": {"require_parameters": True}},
    )
    content = completion.choices[0].message.content
    if not content:
        raise RuntimeError("OpenRouter returned an empty planner decision")
    return PlannerDecision.model_validate_json(content)
