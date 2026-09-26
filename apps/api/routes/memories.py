from fastapi import APIRouter
from agent.memory.consolidation import consolidate
router = APIRouter()

@router.post("/demo/consolidate")
def demo_consolidation():
    return consolidate("INC-042", "Redis pool size reduced from 40 to 8", "Restore the pool and add a deploy guard", [{"hypothesis":"payment provider slowdown","evidence":"Provider p95 was stable and emitted no 5xx errors"}], "Provider failures present as 502s, not pool-wait timeouts")

