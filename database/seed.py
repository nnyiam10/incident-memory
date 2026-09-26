from database.mongodb import database
from agent.memory.consolidation import consolidate

def seed() -> None:
    db = database()
    docs = [m.model_dump(mode="json") for m in consolidate("INC-031", "Leaked Redis connections exhausted checkout's pool", "Close clients and restore the pool", [{"hypothesis":"payment provider slowdown","evidence":"Provider latency stayed normal"}], "Provider failures surface as 502s, not pool-wait timeouts")]
    for doc in docs:
        doc["service"] = "checkout"
    db.memories.delete_many({"provenance.incident_id":"INC-031"})
    db.memories.insert_many(docs)

if __name__ == "__main__": seed()
