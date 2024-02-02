import os
from pathlib import Path

YT_API_KEY = os.environ.get("YT_API_KEY")

API_HOST = os.getenv("API_HOST")
API_PORT = os.getenv("API_PORT")
API_HOST_URL = f"http://{API_HOST}:{API_PORT}"

INGESTED_YT_HISTORY_DATA_PATH = Path("../data/userHistoryData.json")
VIDEO_DETAILS_JSON_PATH = Path("../data/videoDetails.json")
