import functools
import os

from motor.motor_asyncio import AsyncIOMotorClient


@functools.lru_cache
def get_db_client() -> AsyncIOMotorClient:
    url = os.environ.get("MONGODB_URL")
    if url is None:
        raise ValueError("Define 'MONGODB_URL' in .env file.")
    client = AsyncIOMotorClient(
        url,
        serverSelectionTimeoutMS=3000,  # Set timeout to 3 seconds
    )
    return client
