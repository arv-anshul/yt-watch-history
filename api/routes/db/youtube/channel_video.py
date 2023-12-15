from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo import InsertOne, UpdateOne

from api._errors import APIExceptionResponder
from api.configs import DB_NAME, YT_CHANNEL_VIDEO_COLLECTION
from api.models.youtube import YtChannelVideoData
from api.models.youtube.video import YtVideoDetails
from api.routes.db.connect import get_db_client

db_yt_channel_video_route = APIRouter(
    prefix="/channel/video",
    tags=["channel", "channelVideo"],
)


async def get_collection() -> AsyncIOMotorCollection:
    collection = get_db_client()[DB_NAME][YT_CHANNEL_VIDEO_COLLECTION]
    return collection


@db_yt_channel_video_route.post("/")
@APIExceptionResponder
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


@db_yt_channel_video_route.put("/", status_code=204)
@APIExceptionResponder
async def update_channels_videos_data(
    data: list[YtChannelVideoData],
    collection: AsyncIOMotorCollection = Depends(get_collection),
) -> None:
    existing_channels = await collection.find(
        {"channelId": {"$in": [ch_data.channelId for ch_data in data]}}
    ).to_list(None)
    existing_channels_dict = {
        channel["channelId"]: channel for channel in existing_channels
    }

    operations = []
    for ch_data in data:
        existing_channel = existing_channels_dict.get(ch_data.channelId)
        if existing_channel:
            existing_video_ids = set(existing_channel.get("videoIds", []))
            new_video_ids = set(ch_data.videoIds)
            if new_video_ids - existing_video_ids:
                total_ids = list(existing_video_ids | new_video_ids)
                operations.append(
                    UpdateOne(
                        {"channelId": ch_data.channelId},
                        {"$set": {"videoIds": total_ids}},
                    )
                )
        else:
            operations.append(InsertOne(ch_data.model_dump()))

    if operations:
        await collection.bulk_write(operations)


@db_yt_channel_video_route.put(
    "/usingVideosDetails",
    status_code=204,
    description="Insert or Update channel videos data in database using video details.",
)
@APIExceptionResponder
async def update_using_videos_details(
    details: list[YtVideoDetails],
    collection: AsyncIOMotorCollection = Depends(get_collection),
) -> None:
    if not details:
        return
    channel_video_data = YtChannelVideoData.from_video_details(details)

    existing_channels = await collection.find(
        {"channelId": {"$in": [i.channelId for i in channel_video_data]}}
    ).to_list(None)
    existing_channels_dict = {
        channel["channelId"]: channel for channel in existing_channels
    }

    operations = []
    for i in channel_video_data:
        filter_query = {"channelId": i.channelId}
        existing_channel = existing_channels_dict.get(i.channelId)
        if existing_channel:
            existing_video_ids = set(existing_channel.get("videoIds", []))
            new_video_ids = set(i.videoIds)
            if new_video_ids - existing_video_ids:
                total_ids = list(existing_video_ids | new_video_ids)
                operations.append(
                    UpdateOne(filter_query, {"$set": {"videoIds": total_ids}})
                )
        else:
            operations.append(InsertOne(i.model_dump()))

    if operations:
        await collection.bulk_write(operations)


@db_yt_channel_video_route.post(
    "/excludeExistingIds",
    description="Exclude the videosId which are exists in database.",
)
@APIExceptionResponder
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
    id_not_present = list(ids_from_data - ids_from_db)
    if id_not_present:
        return id_not_present
    raise HTTPException(204)
