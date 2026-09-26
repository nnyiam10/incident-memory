from database.mongodb import database
from database.embeddings import embed_texts

def retrieve(query_embedding: list[float], service: str, limit: int = 5) -> list[dict]:
    pipeline = [{"$vectorSearch": {"index": "memory_vector", "path": "embedding", "queryVector": query_embedding, "numCandidates": limit * 20, "limit": limit, "filter": {"service": service, "status": "active"}}}, {"$set": {"score": {"$meta": "vectorSearchScore"}}}, {"$project": {"embedding": 0}}]
    return list(database().memories.aggregate(pipeline))

def retrieve_by_text(query: str, service: str, limit: int = 5) -> list[dict]:
    return retrieve(embed_texts([query])[0], service=service, limit=limit)
