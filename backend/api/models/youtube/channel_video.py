import typing

import polars as pl
from pydantic import BaseModel

if typing.TYPE_CHECKING:
    from api.models.youtube import YtVideoDetails


class YtChannelVideoData(BaseModel):
    channelId: str
    channelTitle: str
    videoIds: list[str]

    @classmethod
    def from_video_details(
        cls, details: list["YtVideoDetails"]
    ) -> typing.Iterator[typing.Self]:
        if len(details) == 0:
            raise ValueError("Empty list of details provided.")

        df = pl.DataFrame([i.model_dump() for i in details]).with_columns(
            pl.col("id").alias("videoId"),
        )
        yield from cls.from_df(df)

    @classmethod
    def from_df(cls, df: pl.DataFrame) -> typing.Iterator[typing.Self]:
        _ = {"channelId", "channelTitle", "videoId"}
        if not all(i in df.columns for i in _):
            raise ValueError(
                "DataFrame must have the required columns: "
                f"{list(_.difference(df.columns))}"
            )
        main_df = (
            df.lazy()
            .drop_nulls("channelId")
            .select("channelTitle", "channelId", "videoId")
            .group_by("channelId")
            .agg(
                pl.col("channelTitle"),
                pl.col("videoId").alias("videoIds"),
            )
            .with_columns(
                pl.col("channelTitle").list.get(0),
            )
            .collect()
        )

        yield from (cls(**i) for i in main_df.iter_rows(named=True))
