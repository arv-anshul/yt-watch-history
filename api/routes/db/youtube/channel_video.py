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


@db_yt_channel_video_route.get("/")
@APIExceptionResponder
async def get_channel(
    channel_id: str,
    collection: AsyncIOMotorCollection = Depends(get_collection),
) -> YtChannelVideoData:
    data = await collection.find_one({"channelId": channel_id})
    if data is None:
        raise HTTPException(
            404,
            {"message": "channelId not found in database.", "channelId": channel_id},
        )
    return data


@db_yt_channel_video_route.post("/")
@APIExceptionResponder
async def get_channels(
    channel_ids: list[str],
    collection: AsyncIOMotorCollection = Depends(get_collection),
) -> list[YtChannelVideoData]:
    data = await collection.find({"channelId": {"$in": channel_ids}}).to_list(None)
    if len(data) != 0:
        return data
    raise HTTPException(
        404,
        {"message": "Details not found for channel_ids.", "channelId": channel_ids},
    )


@db_yt_channel_video_route.put("/", status_code=204)
@APIExceptionResponder
async def update_channel_video_data(
    data: YtChannelVideoData,
    collection: AsyncIOMotorCollection = Depends(get_collection),
) -> None:
    ch_exists = await collection.find_one({"channelId": data.channelId})
    if ch_exists:
        total_ids = list(set(ch_exists["videoIds"]) | set(data.videoIds))
        if len(total_ids) != len(ch_exists["videoIds"]):
            await collection.update_one(
                {"channelId": data.channelId},
                {"$set": {"videoIds": total_ids}},
            )
    else:
        await collection.insert_one(data.model_dump())


@db_yt_channel_video_route.put("/bulk", status_code=204)
@APIExceptionResponder
async def update_channel_video_data_in_bulk(
    data: list[YtChannelVideoData],
    collection: AsyncIOMotorCollection = Depends(get_collection),
) -> None:
    operations = []
    for ch_data in data:
        ch_exists = await collection.find_one({"channelId": ch_data.channelId})
        if ch_exists:
            total_ids = list(set(ch_exists["videoIds"]) | set(ch_data.videoIds))
            if len(total_ids) != len(ch_exists["videoIds"]):
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
    "/bulk/videosDetails",
    status_code=204,
    description="Insert or Update channel videos data in database using video details.",
)
@APIExceptionResponder
async def update_using_video_details(
    details: list[YtVideoDetails],
    collection: AsyncIOMotorCollection = Depends(get_collection),
) -> None:
    if not details:
        return

    operations = []
    for i in YtChannelVideoData.from_video_details(details):
        filter_query = {"channelId": i.channelId}
        ch_exists = await collection.find_one(filter_query)
        if ch_exists:
            total_ids = list(set(i.videoIds) | set(ch_exists["videoIds"]))
            if len(total_ids) != len(ch_exists["videoIds"]):
                operations.append(
                    UpdateOne(filter_query, {"$set": {"videoIds": total_ids}})
                )
        else:
            operations.append(InsertOne(i.model_dump()))
    if operations:
        await collection.bulk_write(operations)


@db_yt_channel_video_route.post(
    "/excludeExistingIds",
    description="Exclude the videosId which are present in database.",
)
@APIExceptionResponder
async def exclude_present_ids(
    data: list[YtChannelVideoData],
    collection: AsyncIOMotorCollection = Depends(get_collection),
) -> list[str]:
    ids_from_data = {j for i in data for j in i.videoIds}
    ch_data = await collection.find(
        {"channelId": {"$in": [i.channelId for i in data]}}
    ).to_list(None)
    ids_from_db = {j for i in ch_data for j in i["videoIds"]}
    id_not_present = list(ids_from_data - ids_from_db)
    if id_not_present:
        return id_not_present
    raise HTTPException(204)
