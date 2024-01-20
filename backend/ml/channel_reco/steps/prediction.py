from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import polars as pl
from sklearn.metrics.pairwise import cosine_similarity

from ml.io import load_object

from ..configs import (
    CH_RECO_TRANSFORMER_DATA_PATH,
    CH_RECO_TRANSFORMER_PATH,
)
from .data import preprocess_data, validate_data

if TYPE_CHECKING:
    from sklearn.compose import ColumnTransformer


def _check_system_objects_exists() -> None:
    if not all(
        i.exists()
        for i in (
            CH_RECO_TRANSFORMER_DATA_PATH,
            CH_RECO_TRANSFORMER_PATH,
        )
    ):
        raise FileNotFoundError("Any channel_reco system object missing.")


def prediction(data: pl.DataFrame) -> pl.DataFrame:
    _check_system_objects_exists()
    if data.height != 1:
        data = preprocess_data(data)
        if data.height != 1:
            raise ValueError("Data must contains only one channel.")
    else:
        validate_data(data)

    transformer: ColumnTransformer = load_object(CH_RECO_TRANSFORMER_PATH)
    transformer_data = pl.read_parquet(CH_RECO_TRANSFORMER_DATA_PATH)

    transformed_data = transformer.transform(data.to_pandas())
    similarity = cosine_similarity(
        np.array(transformer_data["transformed_data"].to_list()),
        transformed_data.toarray(),  # type: ignore
    )
    return transformer_data.select("channelId", "channelTitle").with_columns(
        pl.lit(np.ravel(similarity)).alias("similarity"),
    )
