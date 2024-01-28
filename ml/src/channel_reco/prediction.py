from __future__ import annotations

if __name__ == "__main__":
    from pathlib import Path
    from typing import TYPE_CHECKING

    import dill
    import numpy as np
    import polars as pl
    from sklearn.metrics.pairwise import cosine_similarity

    from .data import clean_data

    if TYPE_CHECKING:
        from sklearn.compose import ColumnTransformer

    print("src.channel_reco.prediction")

    # Importing the same training.json file for ease
    data = pl.read_json("data/channel_reco/training.json")

    transformed_df = pl.read_parquet("data/channel_reco/transformed_df.parquet")
    with Path("data/channel_reco/transformer.dill").open("rb") as f:
        transformer: ColumnTransformer = dill.load(f)

    print(transformed_df["transformed_data"][0].shape)
    print(transformed_df.shape)

    # Prediction :: Transform -> calculate(cosine_similarity)
    # --- --- --- --- --- --- --- --- --- --- --- --- --- --- #

    # Transform: only one channel (at a time)
    one_channel_data = data.filter(pl.col("channelTitle").eq("CampusX"))

    # Concat the channel's data into one row
    one_channel_data = clean_data(one_channel_data)
    transformed_channel = transformer.transform(one_channel_data.to_pandas())

    # Calculate cosine_similarity
    similarity = cosine_similarity(
        np.array(transformed_df["transformed_data"].to_list()),
        transformed_channel.toarray(),  # type: ignore
    )

    # Now concat the calculated similarity to get the similar channels ranking
    similarity_df = (
        transformed_df.select("channelId", "channelTitle")
        .with_columns(
            pl.lit(similarity.ravel()).mul(100).round(2).alias("similarity"),
        )
        .sort("similarity", descending=True)
    )
    print(similarity_df.head(8))
