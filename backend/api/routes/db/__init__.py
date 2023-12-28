from fastapi import APIRouter

from . import ctt, youtube

db_route = APIRouter(prefix="/db", tags=["mongodb"])


db_route.include_router(youtube.db_yt_route)
db_route.include_router(ctt.router)
