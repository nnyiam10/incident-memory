from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from database.harness_versions import create_harness_candidate, get_active_harness_version, list_harness_versions, promote_harness_version
from database.schemas.harness_version import HarnessVersion, MemoryContextPolicy

router = APIRouter()

@router.get("/active", response_model=HarnessVersion)
def active():
    return get_active_harness_version()

@router.get("", response_model=list[HarnessVersion])
def versions():
    return list_harness_versions()

class CreateHarnessRequest(BaseModel):
    version: str
    reasoning_model: str
    allowed_tools: list[str]
    tool_order_policy: str
    context_policy: MemoryContextPolicy
    minimum_evidence_without_memory: int
    minimum_evidence_with_feedback: int
    max_actions: int
    parent_version: str
    created_by: str = "human"

class PromoteRequest(BaseModel):
    confirmed: bool
    approved_by: str = "human"

@router.post("", response_model=HarnessVersion, status_code=201)
def create(request: CreateHarnessRequest):
    if not request.version.strip():
        raise HTTPException(status_code=422, detail="Version is required")
    try:
        return create_harness_candidate(HarnessVersion(status="candidate", **request.model_dump()))
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error

@router.post("/{version}/promote", response_model=HarnessVersion)
def promote(version: str, request: PromoteRequest):
    if not request.confirmed:
        raise HTTPException(status_code=422, detail="Explicit promotion confirmation is required")
    try:
        return promote_harness_version(version, request.approved_by)
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
