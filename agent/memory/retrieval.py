from database.mongodb import database
from database.embeddings import embed_texts

def retrieve(query_embedding: list[float], service: str, limit: int = 5) -> list[dict]:
    pipeline = [{"$vectorSearch": {"index": "memory_vector", "path": "embedding", "queryVector": query_embedding, "numCandidates": limit * 20, "limit": limit, "filter": {"service": service, "status": "active"}}}, {"$set": {"score": {"$meta": "vectorSearchScore"}}}, {"$project": {"embedding": 0}}]
    return list(database().memories.aggregate(pipeline))

def retrieve_by_text(query: str, service: str, limit: int = 5) -> list[dict]:
    return retrieve(embed_texts([query])[0], service=service, limit=limit)


def retrieve_feedback_for_investigation(query: str, service: str, investigation_id: str, limit: int = 3) -> list[dict]:
    pipeline = [
        {"$vectorSearch": {"index": "memory_vector", "path": "embedding", "queryVector": embed_texts([query])[0], "numCandidates": 100, "limit": 50, "filter": {"service": service, "status": "active"}}},
        {"$match": {"type": "human_feedback", "provenance.investigation_id": investigation_id}},
        {"$set": {"score": {"$meta": "vectorSearchScore"}}},
        {"$project": {"_id": 0, "embedding": 0}},
        {"$limit": limit},
    ]
    results = list(database().memories.aggregate(pipeline))
    if results:
        return results
    # Atlas Search indexes update asynchronously. Preserve the exact baseline
    # relationship if a just-written correction is not searchable yet.
    return list(database().memories.find(
        {"type": "human_feedback", "service": service, "status": "active", "provenance.investigation_id": investigation_id},
        {"_id": 0, "embedding": 0},
    ).limit(limit))
