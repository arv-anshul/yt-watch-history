from __future__ import annotations

from typing import TYPE_CHECKING, Iterable

import polars as pl
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile
from pymongo import InsertOne, UpdateOne

from api.configs import DB_NAME, YT_CHANNEL_VIDEO_COLLECTION
from api.models.youtube import YtChannelVideoData
from api.models.youtube.video import YtVideoDetails
from api.routes.db.connect import get_db_client

if TYPE_CHECKING:
    from motor.motor_asyncio import AsyncIOMotorCollection


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
    data: Iterable[YtChannelVideoData],
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
    bg_tasks: BackgroundTasks,
    collection: AsyncIOMotorCollection = Depends(get_collection),
):
    if data:
        bg_tasks.add_task(__update_channels_videos_data, data, collection)


@db_yt_channel_video_route.put(
    "/usingVideosDetails",
    status_code=204,
    description="Insert or Update Multiple Channels Videos Data in Database Using Video Details.",
)
async def update_using_videos_details(
    data: list[YtVideoDetails],
    bg_tasks: BackgroundTasks,
    collection: AsyncIOMotorCollection = Depends(get_collection),
):
    if data:
        ch_video_data = list(YtChannelVideoData.from_video_details(data))
        bg_tasks.add_task(__update_channels_videos_data, ch_video_data, collection)


async def exclude_ids_exists_in_db(
    data: list[YtChannelVideoData],
    collection: AsyncIOMotorCollection,
) -> list[str]:
    ids_from_data = {j for i in data for j in i.videoIds}
    pipeline = [
        {"$match": {"channelId": {"$in": [i.channelId for i in data]}}},
        {"$group": {"_id": None, "videoIds": {"$addToSet": "$videoIds"}}},
    ]
    ch_data = await collection.aggregate(pipeline).to_list(None)
    ids_from_db = {j for i in ch_data[0]["videoIds"] for j in i} if ch_data else set()
    return list(ids_from_data - ids_from_db)


@db_yt_channel_video_route.post(
    "/excludeExistingIds",
    description="Exclude videosIds which already exists in database.",
)
async def exclude_existing_ids_using_list(
    data: list[YtChannelVideoData],
    collection: AsyncIOMotorCollection = Depends(get_collection),
) -> list[str]:
    id_not_exists = await exclude_ids_exists_in_db(data, collection)
    if id_not_exists:
        return id_not_exists
    raise HTTPException(204)


@db_yt_channel_video_route.post(
    "/excludeExistingIds/frame",
    description="Exclude VideosId which exists already in database using dataframe.",
)
async def exclude_ids_exists_in_database_using_df(
    data: UploadFile,
    collection: AsyncIOMotorCollection = Depends(get_collection),
) -> list[str]:
    uploaded_df = pl.read_json(await data.read())

    # Validate dataframe
    _ = {"channelId", "channelTitle", "videoId"}
    if not all(i in uploaded_df.columns for i in _):
        raise HTTPException(
            400,
            {
                "error": "DataFrame must have the required columns.",
                "requiredColumns": _ - set(uploaded_df.columns),
            },
        )

    ch_video_data = list(YtChannelVideoData.from_df(uploaded_df))
    id_not_exists = await exclude_ids_exists_in_db(ch_video_data, collection)
    if id_not_exists:
        return id_not_exists
    raise HTTPException(204)
