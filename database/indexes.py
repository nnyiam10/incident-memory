from database.mongodb import database
from pymongo.operations import SearchIndexModel

MEMORY_VECTOR_INDEX = "memory_vector"
EMBEDDING_DIMENSIONS = 1536

def ensure_indexes() -> None:
    db = database()
    db.memories.create_index([("type", 1), ("service", 1), ("status", 1)])
    db.memories.create_index("provenance.incident_id")
    db.investigations.create_index("incident_id", unique=True)
    db.investigations.create_index("harness_version")
    db.harness_versions.create_index("version", unique=True)
    db.harness_versions.create_index("status")
    db.harness_versions.create_index("status", unique=True, partialFilterExpression={"status": "active"}, name="one_active_harness")
    db.evaluations.create_index([("active_version", 1), ("candidate_version", 1), ("created_at", -1)])

def ensure_vector_index() -> str:
    collection = database().memories
    existing = {index["name"] for index in collection.list_search_indexes()}
    if MEMORY_VECTOR_INDEX in existing:
        return MEMORY_VECTOR_INDEX

    model = SearchIndexModel(
        definition={
            "fields": [
                {
                    "type": "vector",
                    "path": "embedding",
                    "numDimensions": EMBEDDING_DIMENSIONS,
                    "similarity": "cosine",
                },
                {"type": "filter", "path": "service"},
                {"type": "filter", "path": "status"},
            ]
        },
        name=MEMORY_VECTOR_INDEX,
        type="vectorSearch",
    )
    return collection.create_search_index(model=model)
