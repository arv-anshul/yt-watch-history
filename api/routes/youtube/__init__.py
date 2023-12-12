from fastapi import APIRouter

from .video import yt_video_route

yt_route = APIRouter(prefix="/yt", tags=["youtube"])

yt_route.include_router(yt_video_route)
