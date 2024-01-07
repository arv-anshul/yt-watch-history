from __future__ import annotations

from typing import TYPE_CHECKING, Iterator, Self

import polars as pl
from pydantic import BaseModel

if TYPE_CHECKING:
    from api.models.youtube import YtVideoDetails


class YtChannelVideoData(BaseModel):
    channelId: str
    channelTitle: str
    videoIds: list[str]

    @classmethod
    def from_video_details(cls, details: list[YtVideoDetails]) -> Iterator[Self]:
        if len(details) == 0:
            raise ValueError("Empty list of details provided.")

        df = pl.DataFrame([i.model_dump() for i in details]).with_columns(
            pl.col("id").alias("videoId"),
        )
        yield from cls.from_df(df)

    @classmethod
    def from_df(cls, df: pl.DataFrame) -> Iterator[Self]:
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
