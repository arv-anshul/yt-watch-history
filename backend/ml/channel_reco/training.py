from __future__ import annotations

import polars as pl
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.pipeline import FunctionTransformer, Pipeline, make_pipeline

from .data import clean_data, preprocess_data
from .model import get_vectorizer


def training(raw_data: pl.DataFrame) -> tuple[Pipeline, pl.DataFrame]:
    data = preprocess_data(raw_data)
    transformer = get_vectorizer()
    transformed_data = transformer.fit_transform(data.to_pandas())

    pipe = make_pipeline(
        FunctionTransformer(clean_data),
        transformer,
        FunctionTransformer(lambda x: cosine_similarity(transformed_data, x)),
    )
    return pipe, data.select("channelId", "channelTitle")


if __name__ == "__main__":
    from pathlib import Path

    import dill

    print("channel_reco.training")

    # raw_data must contain [channelId, channelTitle, title, tags] columns
    raw_data = pl.read_json("../data/channel_reco/training.json")
    pipe, channels_df = training(raw_data)

    channels_df.write_parquet("../data/channel_reco/channels_df.parquet")
    with Path("../data/channel_reco/transformer_pipe.dill").open("wb") as f:
        dill.dump(pipe, f)
