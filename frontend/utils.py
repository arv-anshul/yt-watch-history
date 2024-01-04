from itertools import islice
from typing import TYPE_CHECKING

import polars as pl

if TYPE_CHECKING:
    from typing import Iterable, Iterator


def batch_iter(iterable: "Iterable", n: int, /) -> "Iterator":
    yield from (list(islice(iterable, i, i + n)) for i in range(0, len(iterable), n))  # type: ignore


# TODO: Create an API endpoint which accepts DataFrame (buffer) to this.
# And remove this function dependency.
def yt_cannel_video_data_from_df(df: pl.DataFrame) -> "Iterator[dict]":
    """Just copied from `backend.api.models.youtube.channel_video` module."""
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

    yield from (i for i in main_df.iter_rows(named=True))
