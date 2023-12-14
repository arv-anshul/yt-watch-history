import asyncio
from typing import Optional

import httpx
from fastapi import APIRouter, HTTPException, Query

from api._errors import APIExceptionResponder
from api._utils import batch_iter
from api.configs import YT_API_KEY_AS_API_HEADER
from api.models.youtube import YtVideoDetails

yt_video_route = APIRouter(prefix="/video", tags=["video"])


async def fetch_one_video(
    key: str,
    ids: str,
    *,
    part: Optional[str] = None,
) -> list[YtVideoDetails]:
    part = "snippet,contentDetails" if part is None else part
    url = f"https://www.googleapis.com/youtube/v3/videos?part={part}&id={ids}&key={key}"

    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        if response.status_code == 400:
            raise HTTPException(400, {"message": "Wrong API key.", "apiKey": key})
        elif response.status_code != 200:
            raise HTTPException(
                400,
                {
                    "message": "Error fetching data from YouTube API.",
                    "ids": ids,
                    "statusCode": response.status_code,
                    "YtApiResponse": response.json(),
                },
            )

        data = response.json()["items"]
    if not data:
        raise HTTPException(204, {"message": "No data after request."})
    return await YtVideoDetails.from_dicts(data)


@yt_video_route.get(
    "/",
    tags=["youtubeApi"],
)
@APIExceptionResponder
async def get_one_video(
    id: str,
    key: str = YT_API_KEY_AS_API_HEADER,
    part: Optional[str] = None,
) -> YtVideoDetails:
    data = await fetch_one_video(key, id, part=part)
    if len(data) == 1:
        return data[0]
    elif len(data) == 0:
        raise HTTPException(204, {"message": "Video details not found.", "id": id})
    else:
        raise HTTPException(400, "Something weired happend.")


@yt_video_route.post(
    "/",
    tags=["youtubeApi"],
)
@APIExceptionResponder
async def get_many_videos(
    ids: list[str],
    n: int = Query(
        200,
        description="Maximum no. of videos details being fetches.",
        gt=1,
    ),
    key: str = YT_API_KEY_AS_API_HEADER,
    part: Optional[str] = None,
) -> list[YtVideoDetails]:
    tasks = []
    for _50_ids in batch_iter(ids[:n], 50):
        vids = fetch_one_video(key, ",".join(_50_ids), part=part)
        tasks.append(vids)
    details = await asyncio.gather(*tasks)
    return [j for i in details for j in i]
