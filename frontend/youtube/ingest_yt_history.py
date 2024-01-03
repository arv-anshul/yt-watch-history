import emoji
import polars as pl

from frontend.configs import INGESTED_YT_HISTORY_DATA_PATH


class IngestYtHistory:
    def __init__(self, path: str | None = None) -> None:
        self.df = pl.read_json(path if path else INGESTED_YT_HISTORY_DATA_PATH)

    def _preprocess_data(self, df: pl.DataFrame) -> pl.DataFrame:
        df = (
            df.lazy()
            .with_columns(
                pl.col("activityControls")
                .list.contains("Web & App Activity")
                .alias("fromWebAppActivity"),
                pl.col("activityControls")
                .list.contains("YouTube search history")
                .alias("fromYtSearchHistActivity"),
                pl.col("activityControls")
                .list.contains("YouTube watch history")
                .alias("fromYtWatchHistActivity"),
                pl.col("subtitles").list.get(0),
                pl.col("title").str.replace(r"Watched |Visited ", ""),
                pl.col("titleUrl").str.extract(r"v=(.?*)").alias("videoId"),
            )
            .with_columns(
                pl.col("subtitles").struct.field("name").alias("channelTitle"),
                pl.col("subtitles")
                .struct.field("url")
                .str.strip_prefix("https://www.youtube.com/channel/")
                .alias("channelId"),
            )
            .filter(
                # Filter videos which are removed from youtube
                pl.col("videoId").is_not_null(),
                pl.col("channelId").is_not_null(),
            )
            .collect()
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

        return df

    def _feature_extraction(self, df: pl.DataFrame) -> pl.DataFrame:
        df = (
            df.lazy()
            .with_columns(
                pl.col("title").str.contains(r"(?i)#short").alias("isShorts"),
                pl.col("time").str.to_datetime(),
                pl.col("title").str.extract_all(r"#\w+").alias("titleTags"),
                pl.col("title")
                .map_elements(lambda x: [e["emoji"] for e in emoji.emoji_list(x)])
                .alias("titleEmojis"),  # List of emoji from title
            )
            .with_columns(
                pl.col("time").dt.hour().alias("hour"),
                pl.col("time").dt.month().alias("month"),
                pl.col("time").dt.weekday().alias("weekday"),
                pl.col("time").dt.year().alias("year"),
                pl.col("time")
                .dt.hour()
                .cut(
                    breaks=[5, 12, 17, 21],
                    labels=["Night", "Morning", "Afternoon", "Evening", "Night"],
                    left_closed=True,
                )
                .alias("daytime"),
            )
            .collect()
        )

        return df

    def _drop_cols(self, df: pl.DataFrame) -> pl.DataFrame:
        drop_cols = [
            "activityControls",
            "details",
            "header",
            "products",
            "subtitles",
            "titleUrl",
        ]
        drop_cols.append("description") if "description" in df.columns else ...
        return df.drop(drop_cols)

    def initiate(self) -> pl.DataFrame:
        """
        Initiate the process to preprocess the data and feature extraction of it.
        """
        df = self._preprocess_data(self.df)
        df = self._feature_extraction(df)
        df = self._drop_cols(df)
        return df

    @classmethod
    def from_ingested_data(cls) -> pl.DataFrame:
        df = pl.read_json(INGESTED_YT_HISTORY_DATA_PATH)
        df = df.with_columns(
            pl.col("time").str.to_datetime(),
        )
        return df
