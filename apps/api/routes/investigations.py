from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from agent.harness.runner import investigate
from database.investigations import get_investigation, list_investigations, save_investigation
from database.schemas.investigation import Investigation
router = APIRouter()

class StartRequest(BaseModel):
    incident_id: str
    observation: str
    scenario: str = "bad_deployment"
    correction: str | None = None

@router.post("")
def start(request: StartRequest):
    state = investigate(**request.model_dump())
    saved = save_investigation(state, scenario=request.scenario)
    state.investigation_id = saved.id
    return state

@router.get("", response_model=list[Investigation])
def list_saved(limit: int = Query(default=20, ge=1, le=100)):
    return list_investigations(limit=limit)

@router.get("/{investigation_id}", response_model=Investigation)
def get_saved(investigation_id: str):
    investigation = get_investigation(investigation_id)
    if investigation is None:
        raise HTTPException(status_code=404, detail="Investigation not found")
    return investigation
