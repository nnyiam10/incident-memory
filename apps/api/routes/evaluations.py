from fastapi import APIRouter, HTTPException, Query

from database.evaluations import list_evaluations, save_evaluation
from database.harness_versions import get_active_harness_version, get_harness_version
from database.schemas.evaluation import HarnessEvaluation
from evals.run_eval import compare_harnesses

router = APIRouter()

@router.post("/harnesses/{candidate_version}", response_model=HarnessEvaluation)
def run_harness_evaluation(candidate_version: str):
    active = get_active_harness_version()
    candidate = get_harness_version(candidate_version)
    if candidate is None:
        raise HTTPException(status_code=404, detail="Harness candidate not found")
    if candidate.status != "candidate":
        raise HTTPException(status_code=409, detail="Only candidate harnesses can be evaluated")
    evaluation = compare_harnesses(active, candidate)
    return save_evaluation(evaluation)

@router.get("", response_model=list[HarnessEvaluation])
def evaluations(candidate_version: str | None = Query(default=None)):
    return list_evaluations(candidate_version)
