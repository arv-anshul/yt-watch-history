from fastapi import APIRouter

from . import youtube

db_route = APIRouter(prefix="/db", tags=["mongodb"])


db_route.include_router(youtube.db_yt_route)
