from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException
from pymongo import InsertOne, UpdateOne

from api.configs import COLLECTION_YT_VIDEO, DB_YOUTUBE
from api.models.youtube import YtVideoDetails
from api.routes.db.connect import get_db_client

if TYPE_CHECKING:
    from motor.motor_asyncio import AsyncIOMotorCollection


db_yt_video_route = APIRouter(prefix="/video", tags=["video"])


async def get_collection() -> AsyncIOMotorCollection:
    collection = get_db_client()[DB_YOUTUBE][COLLECTION_YT_VIDEO]
    return collection


@db_yt_video_route.post(
    "/all",
    description="Get all video details data from database.",
)
async def get_all_video_details(
    collection: AsyncIOMotorCollection = Depends(get_collection),
) -> list[YtVideoDetails]:
    data = await collection.find().to_list(None)
    if not data:
        raise HTTPException(404, {"error": "No data from database."})
    return data


@db_yt_video_route.post(
    "/",
    description="Get Videos Details from Database with VideosId.",
)
async def get_yt_videos_details(
    ids: list[str],
    collection: AsyncIOMotorCollection = Depends(get_collection),
) -> list[YtVideoDetails]:
    details = await collection.find({"id": {"$in": ids}}).to_list(None)
    if details:
        return details
    raise HTTPException(404, {"message": "Details not found in database.", "id": ids})


@db_yt_video_route.put(
    "/",
    status_code=204,
    description="Insert or Update Multiple Video Details.",
)
async def update_videos_details(
    details: list[YtVideoDetails],
    force_update: bool = False,
    collection: AsyncIOMotorCollection = Depends(get_collection),
):
    existing_videos = await collection.find(
        {"id": {"$in": [i.id for i in details]}}
    ).to_list(None)
    existing_video_ids = {video["id"]: video for video in existing_videos}

    operations = []
    for video in details:
        existing_video = existing_video_ids.get(video.id)
        if existing_video is None:
            operations.append(InsertOne(video.model_dump()))
        elif force_update is True:
            operations.append(UpdateOne({"id": video.id}, {"$set": video.model_dump()}))
    if operations:
        await collection.bulk_write(operations)
