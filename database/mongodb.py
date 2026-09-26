import os
from functools import lru_cache
from pymongo import MongoClient

@lru_cache
def database():
    client = MongoClient(os.getenv("MONGODB_URI", "mongodb://localhost:27017"))
    return client[os.getenv("MONGODB_DATABASE", "incident_memory")]

