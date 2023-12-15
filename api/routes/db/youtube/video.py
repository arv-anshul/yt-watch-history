from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo import InsertOne, UpdateOne

from api._errors import APIExceptionResponder
from api.configs import DB_NAME, YT_VIDEO_COLLECTION
from api.models.youtube import YtVideoDetails
from api.routes.db.connect import get_db_client

db_yt_video_route = APIRouter(prefix="/video", tags=["video"])


async def get_collection() -> AsyncIOMotorCollection:
    collection = get_db_client()[DB_NAME][YT_VIDEO_COLLECTION]
    return collection


@db_yt_video_route.post("/")
@APIExceptionResponder
async def get_many_yt_videos(
    ids: list[str],
    collection: AsyncIOMotorCollection = Depends(get_collection),
) -> list[YtVideoDetails]:
    details = await collection.find({"id": {"$in": ids}}).to_list(length=None)
    if details:
        return [YtVideoDetails(**i) for i in details]
    raise HTTPException(404, {"message": "Details not found in database.", "id": ids})


@db_yt_video_route.put(
    "/bulk",
    status_code=204,
    description="Insert or Update the video details.",
)
@APIExceptionResponder
async def update_video_in_bulk(
    details: list[YtVideoDetails],
    force_update: bool = False,
    collection: AsyncIOMotorCollection = Depends(get_collection),
):
    existing_videos = await collection.find(
        {"id": {"$in": [i.id for i in details]}}
    ).to_list(None)
    existing_video_ids = {video["id"]: video for video in existing_videos}

    bulk_operations = []
    for video in details:
        existing_video = existing_video_ids.get(video.id)
        if existing_video:
            if force_update is False:
                continue
            bulk_operations.append(
                UpdateOne({"_id": existing_video["_id"]}, {"$set": video.model_dump()})
            )
        else:
            bulk_operations.append(InsertOne(video.model_dump()))

    if bulk_operations:
        await collection.bulk_write(bulk_operations)
