import os

from fastapi import Header

API_PORT = os.getenv("API_PORT")
API_HOST = os.getenv("API_HOST")
API_HOST_URL = f"http://{API_HOST}:{API_PORT}"

# Database Configs
DB_NAME = "YoutubeDB"
YT_VIDEO_COLLECTION = "YtVideosData"
YT_CHANNEL_VIDEO_COLLECTION = "YtChannelVidData"

DB_CTT = "CttDB"
COLLECTION_CTT_CHANNELS = "CttChannelsData"

# YouTube API configs
YT_API_KEY_AS_API_HEADER = Header(
    alias="YT-API-KEY",
    description="YouTube Data v3 API Key",
    min_length=30,
)
