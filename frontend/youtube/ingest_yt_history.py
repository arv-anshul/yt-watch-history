from io import IOBase
from pathlib import Path

import emoji
import polars as pl

import frontend.constants as C


class IngestYtHistory:
    def __init__(self, source: str | Path | IOBase | bytes) -> None:
        self.df = pl.read_json(source)

    def _preprocess_data(self, df: pl.DataFrame) -> pl.DataFrame:
        # activityControls
        df = df.with_columns(
            pl.col("activityControls")
            .list.contains("YouTube search history")
            .alias("fromYtSearchHistActivity"),
            pl.col("activityControls")
            .list.contains("YouTube watch history")
            .alias("fromYtWatchHistActivity"),
            pl.col("activityControls")
            .list.contains("Web & App Activity")
            .alias("fromWebAppActivity"),
        )

        # title and titleUrl
        df = df.with_columns(
            pl.col("title").str.replace("Watched |Visited ", ""),
            pl.col("titleUrl").str.replace(
                "https://www.youtube.com/watch?v=", "https://youtu.be/", literal=True
            ),
            pl.col("titleUrl").str.extract(r"v=(.?*)").alias("videoId"),
        )

        # details
        if "details" in df.columns:
            df.select(pl.col("details").explode().unique())
            df = df.with_columns(
                pl.col("details")
                .list.get(0)
                .struct.field("name")
                .map_elements(bool)
                .fill_null(False)
                .alias("fromGoogleAds")
            )

        # subtitles
        # > Extract channelTitle & channelUrl
        df = df.with_columns(pl.col("subtitles").list.get(0)).with_columns(
            pl.col("subtitles").struct.field("name").alias("channelTitle"),
            pl.col("subtitles")
            .struct.field("url")
            .str.strip_prefix("https://www.youtube.com/channel/")
            .alias("channelId"),
        )

        return df

    def _feature_extraction(self, df: pl.DataFrame) -> pl.DataFrame:
        # time
        df = df.with_columns(
            pl.col("time").str.to_datetime(),
        ).with_columns(
            pl.col("time").dt.year().alias("year"),
            pl.col("time").dt.month()
            # .map_elements(lambda x: list(calendar.month_name)[int(x)])  # type: ignore
            .alias("month"),
            pl.col("time").dt.weekday()
            # .map_elements(lambda x: list(calendar.day_name)[int(x) - 1])  # type: ignore
            .alias("weekday"),
            pl.col("time").dt.hour().alias("hour"),
        )

        # isShorts
        df = df.with_columns(
            pl.col("title").str.contains("(?i)#short").alias("isShorts"),
        )

        # More feature extraction
        df = self._other_feature_extraction(df)

        return df

    def _other_feature_extraction(self, df: pl.DataFrame) -> pl.DataFrame:
        # tags from title
        df = df.with_columns(
            pl.col("title").str.extract_all(r"#\w+").alias("titleTags"),
        )

        # list of emoji from title
        df = df.with_columns(
            pl.col("title")
            .map_elements(lambda x: [e["emoji"] for e in emoji.emoji_list(x)])  # type: ignore
            .alias("titleEmojis"),
        )

        return df

    def _drop_cols(self, df: pl.DataFrame) -> pl.DataFrame:
        df = df.drop(
            "header",
            "products",
            "activityControls",
            "details",
            "subtitles",
        )

        # description
        if "description" in df.columns:
            df = df.drop("description")

        return df

    def initiate(self) -> pl.DataFrame:
        """
        Initiate the process to preprocess the data and feature extraction of it.
        """
        df = self._preprocess_data(self.df)
        df = self._feature_extraction(df)
        df = self._drop_cols(df)
        df.write_json(C.INGESTED_YT_HISTORY_DATA_PATH, pretty=True, row_oriented=True)
        return df

    @classmethod
    def from_ingested_data(cls, path: Path | str) -> pl.DataFrame:
        df = pl.read_json(path)
        df = df.with_columns(
            pl.col("time").str.to_datetime(),
        )
        return df
