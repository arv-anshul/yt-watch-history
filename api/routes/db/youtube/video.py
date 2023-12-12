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


@db_yt_video_route.get("/")
@APIExceptionResponder
async def get_one_yt_video(
    id: str,
    collection: AsyncIOMotorCollection = Depends(get_collection),
) -> YtVideoDetails:
    details = await collection.find_one({"id": id})
    if details:
        return YtVideoDetails(**details)
    raise HTTPException(404, {"message": "videoId not found in database.", "id": id})


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
    "/",
    status_code=204,
    description="Insert or Update the video details.",
)
@APIExceptionResponder
async def update_one_video(
    details: YtVideoDetails,
    force_update: bool = False,
    collection: AsyncIOMotorCollection = Depends(get_collection),
):
    video_exists = collection.find_one({"id": details.id})
    if video_exists:
        if force_update is False:
            raise HTTPException(
                409,
                {
                    "message": "videoId already exists in the database.",
                    "id": details.id,
                    "force_update": False,
                },
            )
        await collection.update_one({"id": details.id}, {"$set": details.model_dump()})
    else:
        await collection.insert_one(details.model_dump())


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
    operations = []
    for i in details:
        video_exists = await collection.find_one({"id": i.id})
        if video_exists:
            if force_update:
                operations.append(UpdateOne({"id": i.id}, {"$set": i.model_dump()}))
        else:
            operations.append(InsertOne(i.model_dump()))
    if operations:
        await collection.bulk_write(operations)
