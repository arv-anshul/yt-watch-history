from __future__ import annotations

from typing import TYPE_CHECKING

import polars as pl

from .data import preprocess_data
from .model import get_vectorizer

if TYPE_CHECKING:
    from sklearn.compose import ColumnTransformer


def training(raw_data: pl.DataFrame) -> tuple[ColumnTransformer, pl.DataFrame]:
    data = preprocess_data(raw_data)
    transformer = get_vectorizer()
    transformed_data = transformer.fit_transform(data.to_pandas()).toarray()  # type: ignore

    # Combine transformed_data, channelId, channelTitle as DataFrame
    transformed_df = data.select("channelId", "channelTitle").with_columns(
        pl.lit(transformed_data).alias("transformed_data")
    )
    return transformer, transformed_df


if __name__ == "__main__":
    from pathlib import Path

    import dill

    print("channel_reco.training")

    # raw_data must contain [channelId, channelTitle, title, tags] columns
    raw_data = pl.read_json("../data/channel_reco/training.json")
    transformer, transformed_df = training(raw_data)

    print(transformed_df["transformed_data"][0].shape)
    print(transformed_df.shape)

    transformed_df.write_parquet("../data/channel_reco/transformed_df.parquet")
    with Path("../data/channel_reco/transformer.dill").open("wb") as f:
        dill.dump(transformer, f)
