import os

from openai import OpenAI
from pymongo import UpdateOne

from database.mongodb import database

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")


def memory_text(memory: dict) -> str:
    return "\n".join(
        part
        for part in [
            f"Memory type: {memory.get('type', '')}",
            f"Service: {memory.get('service', '')}",
            f"Title: {memory.get('title', '')}",
            f"Content: {memory.get('content', '')}",
        ]
        if part
    )


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    response = OpenAI().embeddings.create(model=EMBEDDING_MODEL, input=texts)
    return [item.embedding for item in sorted(response.data, key=lambda item: item.index)]


def embed_memories(force: bool = False) -> int:
    query = {} if force else {"embedding": {"$exists": False}}
    memories = list(database().memories.find(query))
    vectors = embed_texts([memory_text(memory) for memory in memories])
    if not vectors:
        return 0

    operations = [
        UpdateOne(
            {"_id": memory["_id"]},
            {"$set": {"embedding": vector, "embedding_model": EMBEDDING_MODEL}},
        )
        for memory, vector in zip(memories, vectors, strict=True)
    ]
    database().memories.bulk_write(operations)
    return len(operations)


if __name__ == "__main__":
    print(f"Embedded {embed_memories()} memories with {EMBEDDING_MODEL}")
