from __future__ import annotations

if __name__ == "__main__":
    from pathlib import Path
    from typing import TYPE_CHECKING

    import dill
    import polars as pl

    if TYPE_CHECKING:
        from sklearn.pipeline import Pipeline

    print("channel_reco.prediction")

    # Importing the same training.json file for ease
    data = pl.read_json("../data/channel_reco/training.json")

    channels_df = pl.read_parquet("../data/channel_reco/channels_df.parquet")
    with Path("../data/channel_reco/transformer_pipe.dill").open("rb") as f:
        pipe: Pipeline = dill.load(f)

    # Prediction :: pipe.transform(cosine_similarity(data))
    # --- --- --- --- --- --- --- --- --- --- --- --- --- --- #

    # Transform: only one channel (at a time)
    one_channel_data = data.filter(pl.col("channelTitle").eq("CampusX"))

    # Calculate cosine_similarity
    similarity = pipe.transform(one_channel_data)

    # Now concat the calculated similarity to get the similar channels ranking
    similarity_df = (
        channels_df.select("channelId", "channelTitle")
        .with_columns(
            pl.lit(similarity.ravel()).mul(100).round(2).alias("similarity"),
        )
        .sort("similarity", descending=True)
    )
    print(similarity_df.head(8))
