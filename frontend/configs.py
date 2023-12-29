import os
from pathlib import Path

YT_API_KEY = os.environ.get("YT_API_KEY")

INGESTED_YT_HISTORY_DATA_PATH = Path("data/userHistoryData.json")
VIDEO_DETAILS_JSON_PATH = Path("data/videoDetails.json")
CATEGORY_ID_MAP_PATH = Path("data/categoryIdMap.json")
