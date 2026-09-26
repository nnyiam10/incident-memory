# Incident Memory

Incident Memory is a safe production-debugging agent that learns how an engineering team investigates incidents. The demo uses a three-service e-commerce system (`checkout`, `inventory`, and `payments`) and makes MongoDB the durable source of truth for incidents, hypotheses, evidence, feedback, and evolving agent memory.

## The demo story

1. Trigger: “Checkout requests started timing out after the latest deploy.”
2. The agent reads simulated logs, metrics, deploy history, code context, and prior memories.
3. The first run explores several hypotheses. An engineer corrects one mistaken assumption.
4. Consolidation stores the correction with provenance—not as an undifferentiated transcript.
5. The second run recalls it, checks the deployment diff first, avoids the provider-status dead end, and reaches the root cause faster.

The dashboard's **Comparison** view makes the improvement visible: fewer actions, no repeated dead ends, and faster diagnosis.

## Run locally

```bash
cp .env.example .env
npm install
npm run dev
```

Open the local URL printed by the command. The dashboard works immediately with representative demo state.

For the API and MongoDB-backed flow:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
docker compose up mongodb -d
npm run api
```

API documentation is at `http://localhost:8000/docs`. Try `GET /incidents/demo`, then `POST /investigations` with:

```json
{
  "incident_id": "INC-042",
  "observation": "Checkout requests started timing out after the latest deploy.",
  "scenario": "bad_deployment",
  "correction": "Provider failures present as 502s, not pool-wait timeouts."
}
```

## Memory model

- **Episodic:** a complete incident outcome and its provenance.
- **Semantic:** stable facts about services and dependency signatures.
- **Procedural:** reusable investigation sequences promoted from successful runs.
- **Negative:** failed hypotheses plus the evidence that ruled them out.
- **Human feedback:** explicit corrections and team preferences at confidence 1.0.

Every memory has confidence, provenance, usage count, contradiction links, lifecycle status, and optional `supersedes`. New evidence revises or supersedes an old belief instead of silently storing a conflict.

## Safety boundary

The agent may search logs and code, query metrics and deployments, and run tests against the sandbox. It cannot mutate production. `agent/policies/guardrails.py` is the enforcement point; remediation is proposed for human approval.

## Project map

- `app/` — interactive investigation dashboard
- `apps/api/` — FastAPI surface
- `agent/harness/` — bounded investigation loop and serializable state
- `agent/memory/` — typed retrieval, consolidation, contradiction handling
- `agent/policies/` — tool allow-list and sandbox boundary
- `database/` — MongoDB connection, schemas, and index setup
- `sandbox/incidents/` — three reproducible failure fixtures
- `tests/` — learning behavior and consolidation checks

## Next production steps

Create the Atlas `memory_vector` index, replace simulated tools with read-only observability adapters, stream investigation events from the worker, and wire the dashboard to the API. Keep the same schemas and safety boundary.

