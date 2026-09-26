from fastapi import APIRouter
from pydantic import BaseModel
from agent.harness.runner import investigate
from database.investigations import save_investigation
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
