from datetime import datetime, timezone
from agent.policies.models import REASONING_MODEL
from database.mongodb import database
from database.schemas.harness_version import HarnessVersion, MemoryContextPolicy

CURRENT_HARNESS_VERSION = "v0.4.0"

def default_harness_version() -> HarnessVersion:
    return HarnessVersion(version=CURRENT_HARNESS_VERSION, status="active", reasoning_model=REASONING_MODEL, allowed_tools=["query_metrics", "search_logs", "get_deployments"], tool_order_policy="symptom_discriminator_first", context_policy=MemoryContextPolicy(), minimum_evidence_without_memory=3, minimum_evidence_with_feedback=2, max_actions=20, promoted_at=datetime.now(timezone.utc))

def get_active_harness_version() -> HarnessVersion:
    collection = database().harness_versions
    document = collection.find_one({"status": "active"}, sort=[("promoted_at", -1)])
    if document:
        document.pop("_id", None)
        return HarnessVersion.model_validate(document)
    harness = default_harness_version()
    collection.update_one({"version": harness.version}, {"$setOnInsert": harness.model_dump(mode="json")}, upsert=True)
    return harness

def list_harness_versions() -> list[HarnessVersion]:
    versions = []
    for document in database().harness_versions.find().sort("created_at", -1):
        document.pop("_id", None)
        versions.append(HarnessVersion.model_validate(document))
    return versions

def get_harness_version(version: str) -> HarnessVersion | None:
    document = database().harness_versions.find_one({"version": version})
    if not document:
        return None
    document.pop("_id", None)
    return HarnessVersion.model_validate(document)

def create_harness_candidate(candidate: HarnessVersion) -> HarnessVersion:
    if candidate.status != "candidate":
        raise ValueError("New harness versions must start as candidates")
    if database().harness_versions.find_one({"version": candidate.version}):
        raise ValueError(f"Harness version {candidate.version} already exists")
    database().harness_versions.insert_one(candidate.model_dump(mode="json"))
    return candidate

def promote_harness_version(version: str, approved_by: str) -> HarnessVersion:
    collection = database().harness_versions
    candidate = collection.find_one({"version": version, "status": "candidate"})
    if not candidate:
        raise ValueError("Only an existing candidate can be promoted")
    active = collection.find_one({"status": "active"})
    if not active:
        raise ValueError("No active harness exists")
    from database.evaluations import latest_passing_evaluation
    if not latest_passing_evaluation(active["version"], version):
        raise ValueError("Candidate must pass evaluation against the current active harness before promotion")
    now = datetime.now(timezone.utc)
    collection.update_many({"status": "active"}, {"$set": {"status": "retired"}})
    collection.update_one(
        {"version": version, "status": "candidate"},
        {"$set": {"status": "active", "promoted_at": now.isoformat(), "promoted_by": approved_by}},
    )
    candidate.update({"status": "active", "promoted_at": now, "promoted_by": approved_by, "evaluation_status": "passed"})
    candidate.pop("_id", None)
    return HarnessVersion.model_validate(candidate)
