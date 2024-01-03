import re

import polars as pl
import polars.selectors as cs

from frontend.configs import INGESTED_YT_HISTORY_DATA_PATH, VIDEO_DETAILS_JSON_PATH

CATEGORY_ID_MAP = {
    "1": "Film & Animation",
    "2": "Autos & Vehicles",
    "10": "Music",
    "15": "Pets & Animals",
    "17": "Sports",
    "18": "Short Movies",
    "19": "Travel & Events",
    "20": "Gaming",
    "21": "Videoblogging",
    "22": "People & Blogs",
    "23": "Comedy",
    "24": "Entertainment",
    "25": "News & Politics",
    "26": "Howto & Style",
    "27": "Education",
    "28": "Science & Technology",
    "29": "Nonprofits & Activism",
    "30": "Movies",
    "31": "Anime/Animation",
    "32": "Action/Adventure",
    "33": "Classics",
    "34": "Comedy",
    "35": "Documentary",
    "36": "Drama",
    "37": "Family",
    "38": "Foreign",
    "39": "Horror",
    "40": "Sci-Fi/Fantasy",
    "41": "Thriller",
    "42": "Shorts",
    "43": "Shows",
    "44": "Trailers",
}


class VideoDetails:
    def __init__(
        self,
        ingested_history_data_path: str | None = None,
        video_details_data_path: str | None = None,
    ) -> None:
        ingested_hist_df = pl.read_json(
            ingested_history_data_path
            if ingested_history_data_path
            else INGESTED_YT_HISTORY_DATA_PATH
        )
        video_details_df = pl.read_json(
            video_details_data_path
            if video_details_data_path
            else VIDEO_DETAILS_JSON_PATH
        )
        category_id_df = pl.DataFrame._from_dict(CATEGORY_ID_MAP).transpose(
            include_header=True,
            header_name="categoryId",
            column_names=["categoryName"],
        )
        self.df = ingested_hist_df.join(
            video_details_df, left_on="videoId", right_on="id"
        ).join(category_id_df, on="categoryId")

    def __handle_duration(self, x: str):
        total_sec = 0
        hr = re.search(r"(\d+)H", x)  # Hours
        total_sec += int(hr.group(1)) * 3600 if hr else 0
        min = re.search(r"(\d+)M", x)  # Minutes
        total_sec += int(min.group(1)) * 60 if min else 0
        sec = re.search(r"(\d+)S", x)  # Seconds
        total_sec += int(sec.group(1)) if sec else 0
        return total_sec

    def _data_cleaning(self, df: pl.DataFrame) -> pl.DataFrame:
        df = df.with_columns(
            pl.col("publishedAt").str.to_datetime(),
            pl.col("duration")
            .map_elements(self.__handle_duration, pl.Int64)
            .alias("durationInSec"),
            pl.col("duration").str.contains("D").alias("durationHasDay"),
            pl.col("tags")
            .is_null()
            .add(pl.col("isShorts"))
            .cast(bool)
            .alias("isShorts"),
        )

        return df

    def _drop_cols(self, df: pl.DataFrame) -> pl.DataFrame:
        drop_cols = [
            "duration",
            "categoryId",
            cs.ends_with("_right"),
        ]
        return df.drop(drop_cols)

    def initiate(self) -> pl.DataFrame:
        df = self._data_cleaning(self.df)
        df = self._drop_cols(df)
        return df
