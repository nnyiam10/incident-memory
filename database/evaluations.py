from database.mongodb import database
from database.schemas.evaluation import HarnessEvaluation

def save_evaluation(evaluation: HarnessEvaluation) -> HarnessEvaluation:
    database().evaluations.insert_one(evaluation.model_dump(mode="json"))
    database().harness_versions.update_one(
        {"version": evaluation.candidate_version},
        {"$set": {"evaluation_status": "passed" if evaluation.passed else "failed", "latest_evaluation_id": evaluation.id}},
    )
    return evaluation

def latest_passing_evaluation(active_version: str, candidate_version: str) -> HarnessEvaluation | None:
    document = database().evaluations.find_one({"active_version": active_version, "candidate_version": candidate_version, "passed": True}, sort=[("created_at", -1)])
    if not document:
        return None
    document.pop("_id", None)
    return HarnessEvaluation.model_validate(document)

def list_evaluations(candidate_version: str | None = None) -> list[HarnessEvaluation]:
    query = {"candidate_version": candidate_version} if candidate_version else {}
    results = []
    for document in database().evaluations.find(query).sort("created_at", -1):
        document.pop("_id", None)
        results.append(HarnessEvaluation.model_validate(document))
    return results
