from fastapi import APIRouter
from database.schemas.incident import Incident
router = APIRouter()

@router.post("")
def create_incident(incident: Incident): return incident

@router.get("/demo")
def demo(): return Incident(id="INC-042", title="Checkout requests timing out", description="Started after latest deploy", service="checkout", symptoms=["p95 > 8s", "Redis pool waiters rising"])

