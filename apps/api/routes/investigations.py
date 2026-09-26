from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from agent.harness.runner import investigate
from database.investigations import attach_correction, get_investigation, list_investigations, save_investigation
from database.memories import save_human_feedback
from database.schemas.investigation import Investigation
router = APIRouter()

class StartRequest(BaseModel):
    incident_id: str
    observation: str
    scenario: str = "auto"
    correction: str | None = None

class CorrectionRequest(BaseModel):
    correction: str
    author: str = "human"

class CorrectionResponse(BaseModel):
    investigation_id: str
    memory_id: str
    memory_type: str
    embedding_model: str
    indexed_by: str

@router.post("")
def start(request: StartRequest):
    state = investigate(**request.model_dump())
    saved = save_investigation(state, scenario=request.scenario)
    state.investigation_id = saved.id
    return state

@router.get("", response_model=list[Investigation])
def list_saved(limit: int = Query(default=20, ge=1, le=100)):
    return list_investigations(limit=limit)

@router.post("/{investigation_id}/corrections", response_model=CorrectionResponse)
def add_correction(investigation_id: str, request: CorrectionRequest):
    correction = request.correction.strip()
    if not correction:
        raise HTTPException(status_code=422, detail="Correction cannot be empty")
    investigation = get_investigation(investigation_id)
    if investigation is None:
        raise HTTPException(status_code=404, detail="Investigation not found")
    if not investigation.complete:
        raise HTTPException(status_code=409, detail="Corrections require a completed investigation")
    memory = save_human_feedback(investigation, correction, request.author)
    attach_correction(investigation_id, correction, memory.id)
    from agent.policies.models import EMBEDDING_MODEL
    return CorrectionResponse(
        investigation_id=investigation_id,
        memory_id=memory.id,
        memory_type=memory.type.value,
        embedding_model=EMBEDDING_MODEL,
        indexed_by="memory_vector",
    )

@router.get("/{investigation_id}", response_model=Investigation)
def get_saved(investigation_id: str):
    investigation = get_investigation(investigation_id)
    if investigation is None:
        raise HTTPException(status_code=404, detail="Investigation not found")
    return investigation
