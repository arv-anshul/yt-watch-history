from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo import UpdateOne

from backend.api import configs
from backend.api.models.ctt import CttChannelData

from .connect import get_db_client

router = APIRouter(prefix="/ctt", tags=["ctt"])


def get_collection():
    client = get_db_client()
    collection = client[configs.DB_CTT][configs.COLLECTION_CTT_CHANNELS]
    return collection


@router.post(
    "/",
    description="Get all CttChannelData from database.",
)
async def get_all_channel_data(
    collection: AsyncIOMotorCollection = Depends(get_collection),
) -> list[CttChannelData]:
    data = await collection.find().to_list(None)
    if not data:
        raise HTTPException(404, {"error": "No data from database."})
    return data


@router.put(
    "/",
    status_code=204,
    description="Update or Insert one CttChannelData into database.",
)
async def update_one_channel_data(
    data: CttChannelData,
    collection: AsyncIOMotorCollection = Depends(get_collection),
):
    await collection.update_one(
        {"channelId": data.channelId}, {"$set": data.model_dump()}, upsert=True
    )


@router.put(
    "/many",
    status_code=204,
    description="Update or Insert CttChannelData in many into database.",
)
async def update_many_channels_data(
    data: list[CttChannelData],
    bg_tasks: BackgroundTasks,
    collection: AsyncIOMotorCollection = Depends(get_collection),
):
    if not data:
        raise HTTPException(400, {"error": "Provide data to add into database."})

    async def perform_bulk_write(data: list[CttChannelData]):
        operations = [
            UpdateOne({"channelId": i.channelId}, {"$set": i.model_dump()}, upsert=True)
            for i in data
        ]
        await collection.bulk_write(operations)

    bg_tasks.add_task(perform_bulk_write, data)
