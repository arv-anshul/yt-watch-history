from fastapi import Header

# Config for development
API_HOST = "localhost"
API_PORT = 8000
API_RELOAD = False
API_HOST_URL = f"http://{API_HOST}:{API_PORT}"  # FastAPI localhost URL

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
