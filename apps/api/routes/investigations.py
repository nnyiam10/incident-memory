from fastapi import APIRouter
from pydantic import BaseModel
from agent.harness.runner import investigate
router = APIRouter()

class StartRequest(BaseModel):
    incident_id: str
    observation: str
    scenario: str = "bad_deployment"
    correction: str | None = None

@router.post("")
def start(request: StartRequest): return investigate(**request.model_dump())

