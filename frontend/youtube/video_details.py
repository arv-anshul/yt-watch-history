import re

import polars as pl

from frontend.configs import (
    CATEGORY_ID_MAP_PATH,
    INGESTED_YT_HISTORY_DATA_PATH,
    VIDEO_DETAILS_JSON_PATH,
)


class VideoDetails:
    def __init__(self) -> None:
        __df = pl.read_json(INGESTED_YT_HISTORY_DATA_PATH)
        __vdf = pl.read_json(VIDEO_DETAILS_JSON_PATH)
        __cat_id_df = pl.read_json(CATEGORY_ID_MAP_PATH).transpose(
            include_header=True,
            header_name="categoryId",
            column_names=["categoryName"],
        )
        self.df = __df.join(
            __vdf.drop("title", "channelTitle", "channelId"),
            left_on="videoId",
            right_on="id",
        ).join(__cat_id_df, on="categoryId")

    def __handle_duration(self, x: str):
        total_sec = 0
        # Hours
        hr = re.search(r"(\d+)H", x)
        total_sec += int(hr.group(1)) * 3600 if hr else 0
        # Minutes
        min = re.search(r"(\d+)M", x)
        total_sec += int(min.group(1)) * 60 if min else 0
        # Seconds
        sec = re.search(r"(\d+)S", x)
        total_sec += int(sec.group(1)) if sec else 0
        return total_sec

    def __data_cleaning(self, df: pl.DataFrame) -> pl.DataFrame:
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
            pl.col("hour")
            .cut(
                breaks=[5, 12, 17, 21],
                labels=["Night", "Morning", "Afternoon", "Evening", "Night"],
                left_closed=True,
            )
            .alias("daytime"),
        ).drop("duration", "categoryId")

        return df

    def initiate(self) -> pl.DataFrame:
        df = self.__data_cleaning(self.df)
        return df
