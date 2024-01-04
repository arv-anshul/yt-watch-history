import asyncio

import httpx
from fastapi import APIRouter, HTTPException, Query

from api._utils import batch_iter
from api.configs import YT_API_KEY_AS_API_HEADER
from api.models.youtube import YtVideoDetails

yt_video_route = APIRouter(prefix="/video", tags=["video"])


async def fetch_video_details_from_yt_api(
    key: str,
    ids: str,
    *,
    part: str | None = None,
) -> list[YtVideoDetails]:
    part = "snippet,contentDetails" if part is None else part
    url = f"https://www.googleapis.com/youtube/v3/videos?part={part}&id={ids}&key={key}"

    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        if response.status_code == 400:
            raise HTTPException(400, {"message": "Wrong API key.", "apiKey": key})
        if response.status_code != 200:
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


@yt_video_route.post(
    "/",
    tags=["youtubeApi"],
    description="Get Multiple Videos Deatails using YouTube API.",
)
async def get_videos_details_from_yt_api(
    ids: list[str],
    limit: int = Query(
        200,
        description="Maximum No. of Videos Details being Fetch.",
        gt=1,
        le=400,
    ),
    key: str = YT_API_KEY_AS_API_HEADER,
    part: str | None = None,
) -> list[YtVideoDetails]:
    tasks = []
    for _50_ids in batch_iter(ids[:limit], 50):
        vids = fetch_video_details_from_yt_api(key, ",".join(_50_ids), part=part)
        tasks.append(vids)
    details = await asyncio.gather(*tasks)
    return [j for i in details for j in i]
