from __future__ import annotations

import os
from typing import TYPE_CHECKING

from fastapi import Header

from errors import ENVNotFoundError

if TYPE_CHECKING:
    from typing import Final

API_PORT: Final[str] = os.getenv("API_PORT")  # type: ignore
API_HOST: Final[str] = os.getenv("API_HOST")  # type: ignore
API_HOST_URL: Final = f"http://{API_HOST}:{API_PORT}"

# Database Configs
MONGODB_URL: Final[str] = os.getenv("MONGODB_URL")  # type: ignore
DB_NAME: Final = "YoutubeDB"
YT_VIDEO_COLLECTION: Final = "YtVideosData"
YT_CHANNEL_VIDEO_COLLECTION: Final = "YtChannelVidData"

DB_CTT: Final = "CttDB"
COLLECTION_CTT_CHANNELS: Final = "CttChannelsData"

# YouTube API configs
YT_API_KEY_AS_API_HEADER = Header(
    alias="YT-API-KEY",
    description="YouTube Data v3 API Key",
    min_length=30,
)


def check_setup_settings() -> None:
    """Check settings before intializing the app."""
    if not API_PORT:
        raise ENVNotFoundError("API_PORT")
    if not API_HOST:
        raise ENVNotFoundError("API_HOST")
    if not MONGODB_URL:
        raise ENVNotFoundError("MONGODB_URL")
