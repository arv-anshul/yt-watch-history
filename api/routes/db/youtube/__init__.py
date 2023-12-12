from fastapi import APIRouter

from .channel_video import db_yt_channel_video_route
from .video import db_yt_video_route

db_yt_route = APIRouter(prefix="/yt", tags=["youtube"])

db_yt_route.include_router(db_yt_video_route)
db_yt_route.include_router(db_yt_channel_video_route)
