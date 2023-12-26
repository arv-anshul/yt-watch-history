import typing

from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo import InsertOne, UpdateOne

from backend.api.configs import DB_NAME, YT_CHANNEL_VIDEO_COLLECTION
from backend.api.models.youtube import YtChannelVideoData
from backend.api.models.youtube.video import YtVideoDetails
from backend.api.routes.db.connect import get_db_client

db_yt_channel_video_route = APIRouter(
    prefix="/channel/video",
    tags=["channel", "channelVideo"],
)


async def get_collection() -> AsyncIOMotorCollection:
    collection = get_db_client()[DB_NAME][YT_CHANNEL_VIDEO_COLLECTION]
    return collection


@db_yt_channel_video_route.post(
    "/",
    description="Get multiple channels videos data from database.",
)
async def get_channels_videos_data(
    channel_ids: list[str],
    collection: AsyncIOMotorCollection = Depends(get_collection),
) -> list[YtChannelVideoData]:
    data = await collection.find({"channelId": {"$in": channel_ids}}).to_list(None)
    if data:
        return data
    raise HTTPException(
        404,
        {"message": "Details not found for channel_ids.", "channelId": channel_ids},
    )


async def __update_channels_videos_data(
    data: typing.Iterable[YtChannelVideoData],
    collection: AsyncIOMotorCollection,
) -> None:
    existing_channels = await collection.find(
        {"channelId": {"$in": [ch_data.channelId for ch_data in data]}}
    ).to_list(None)
    existing_channels_dict = {
        channel["channelId"]: channel for channel in existing_channels
    }

    operations = []
    for i in data:
        existing_channel = existing_channels_dict.get(i.channelId)
        if existing_channel is None:
            operations.append(InsertOne(i.model_dump()))
            continue
        existing_video_ids = set(existing_channel.get("videoIds", []))
        new_video_ids = set(i.videoIds)
        if new_video_ids - existing_video_ids:
            operations.append(
                UpdateOne(
                    {"channelId": i.channelId},
                    {"$set": {"videoIds": list(existing_video_ids | new_video_ids)}},
                )
            )
    if operations:
        await collection.bulk_write(operations)


@db_yt_channel_video_route.put(
    "/",
    status_code=204,
    description="Update or Insert Channel Data into Database.",
)
async def update_channels_videos_data(
    data: list[YtChannelVideoData],
    collection: AsyncIOMotorCollection = Depends(get_collection),
) -> None:
    if data:
        await __update_channels_videos_data(data, collection)


@db_yt_channel_video_route.put(
    "/usingVideosDetails",
    status_code=204,
    description="Insert or Update Multiple Channels Videos Data in Database Using Video Details.",
)
async def update_using_videos_details(
    data: list[YtVideoDetails],
    collection: AsyncIOMotorCollection = Depends(get_collection),
) -> None:
    if data:
        ch_video_data = list(YtChannelVideoData.from_video_details(data))
        await __update_channels_videos_data(ch_video_data, collection)


@db_yt_channel_video_route.post(
    "/excludeExistingIds",
    description="Exclude VideosId Which are Exists in Database.",
)
async def exclude_ids_exists_in_database(
    data: list[YtChannelVideoData],
    collection: AsyncIOMotorCollection = Depends(get_collection),
) -> list[str]:
    ids_from_data = {j for i in data for j in i.videoIds}
    pipeline = [
        {"$match": {"channelId": {"$in": [i.channelId for i in data]}}},
        {"$group": {"_id": None, "videoIds": {"$addToSet": "$videoIds"}}},
    ]
    ch_data = await collection.aggregate(pipeline).to_list(None)
    ids_from_db = {j for i in ch_data[0]["videoIds"] for j in i} if ch_data else set()
    id_not_exists = list(ids_from_data - ids_from_db)
    if id_not_exists:
        return id_not_exists
    raise HTTPException(204)
