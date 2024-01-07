import functools

from motor.motor_asyncio import AsyncIOMotorClient

from api.configs import MONGODB_URL


@functools.lru_cache
def get_db_client() -> AsyncIOMotorClient:
    client = AsyncIOMotorClient(
        MONGODB_URL,
        serverSelectionTimeoutMS=3000,  # Set timeout to 3 seconds
    )
    return client
