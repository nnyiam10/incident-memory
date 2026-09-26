# Incident Memory

Incident Memory is a production-debugging agent that learns how an engineering team investigates incidents. It preserves previous outcomes, successful procedures, failed hypotheses, and human corrections so each related investigation can become faster and more accurate.

MongoDB Atlas is the durable source of truth for investigations, evidence, feedback, harness versions, evaluations, and organizational memory.

## Why it exists

Engineering teams repeatedly solve the same production problems because useful knowledge is scattered across logs, tickets, incident conversations, and individual engineers.

Traditional postmortems usually preserve the final root cause, but not:

- Which hypotheses were attempted
- What evidence ruled them out
- Which diagnostic sequence worked
- What assumptions engineers later corrected

Incident Memory captures that reasoning and applies it during future incidents.

## How it works

1. An engineer submits a production symptom.
2. The incident description is converted into an embedding.
3. MongoDB Atlas Vector Search retrieves semantically relevant memories.
4. The active harness selects safe diagnostic actions.
5. Every action is validated against an allow-list.
6. The agent gathers evidence from simulated logs, metrics, and deployment history.
7. It updates hypotheses and produces an evidence-backed diagnosis.
8. The completed investigation is consolidated into durable memory.
9. Human corrections are embedded and retrieved during related incidents.
10. Candidate harness strategies are evaluated before promotion.

## Demo scenarios

The sandbox includes three reproducible failures:

- Redis connection exhaustion
- Malformed deployment configuration
- Slow external payment API

The Comparison view demonstrates the learning loop:

1. Run an incident.
2. Correct a mistaken assumption.
3. Run a related incident.
4. Observe fewer actions, fewer dead ends, and a faster diagnosis.

## Memory model

Memory is stored as typed MongoDB documents rather than undifferentiated conversation transcripts.

- **Episodic:** Outcomes from individual incidents
- **Semantic:** Stable facts about services and dependencies
- **Procedural:** Investigation strategies that previously worked
- **Negative:** Failed hypotheses and the evidence that ruled them out
- **Human feedback:** Explicit corrections and team-specific knowledge

Each memory can include:

- Confidence
- Service
- Evidence provenance
- Incident and investigation identifiers
- Harness version
- Usage count
- Contradiction references
- Lifecycle status
- Supersession relationships
- Vector embedding

## Harness evolution

Organizational memory remains global, while the agent’s operating strategy is versioned independently.

A harness version controls:

- Tool-order policy
- Eligible memory context
- Memory retrieval limit
- Evidence thresholds
- Maximum diagnostic actions
- Allowed tools
- Reasoning model

The supported tool-order policies are:

- **Symptom Discriminator First:** Prioritize evidence that separates competing causes.
- **Memory Guided First:** Let relevant past lessons influence the initial diagnostic path.

Candidate harnesses are evaluated against all three failure scenarios. Promotion is permitted only when:

- Diagnostic accuracy remains correct
- Accuracy does not regress
- Diagnostic actions do not increase
- Diagnosis time does not increase
- At least one efficiency metric improves

## Safety boundary

Incident Memory performs read-only diagnostics against a sandbox.

The active harness currently exposes:

- Query Metrics
- Search Logs
- Get Deployments

Every model-proposed action must:

1. Appear in the active harness’s allow-list
2. Be implemented by the controlled executor
3. Remain within the action budget
4. Target the sandbox

The agent cannot mutate production. It produces a remediation plan for human review.

## Technology

- **MongoDB Atlas:** Investigations, evidence, feedback, memory, harness versions, and evaluations
- **Atlas Vector Search:** Semantic memory retrieval
- **OpenAI models through OpenRouter:** Planning, hypothesis updates, and diagnosis
- **FastAPI:** Investigation and memory API
- **Vinext/React:** Interactive dashboard
- **Python:** Agent harness, consolidation, evaluation, and persistence

## Project structure

```text
incident-memory/
├── app/                  # Vinext/React dashboard
├── apps/api/             # FastAPI routes
├── agent/
│   ├── harness/          # Investigation loop, state, planning, and budgets
│   ├── memory/           # Retrieval and consolidation
│   ├── policies/         # Guardrails and model configuration
│   ├── prompts/          # Reasoning and reflection prompts
│   └── tools/            # Simulated diagnostic adapters
├── database/             # Atlas connection, schemas, indexes, and seed data
├── evals/                # Harness evaluation scenarios
├── sandbox/incidents/    # Reproducible failure fixtures
└── tests/                # Agent, memory, evaluation, and integration tests
