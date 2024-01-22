from typing import Literal

import polars as pl

from ml.io import dump_object

from ..configs import CH_RECO_TRANSFORMER_DATA_PATH, CH_RECO_TRANSFORMER_PATH
from .data import ingest_data_from_db, ingest_data_from_file, preprocess_data
from .model import get_vectorizer


def training(
    input_data: Literal["db", "file"],
):
    if input_data == "db":
        df = ingest_data_from_db()
    elif input_data == "file":
        df = ingest_data_from_file()
    else:
        raise ValueError(
            f"{input_data!r} is not valid for '--input-data'. Use '--help' command."
        )

    df = preprocess_data(df)
    transformer = get_vectorizer()
    transformed_data = transformer.fit_transform(df.to_pandas())

    # Combine transformed_data, channelId, channelTitle as DataFrame
    title_tags_trf_df = df.select("channelId", "channelTitle").with_columns(
        pl.lit(transformed_data.toarray()).alias("transformed_data")  # type: ignore
    )

    dump_object(transformer, CH_RECO_TRANSFORMER_PATH)
    # Export dataframe as parquet format for lesser size
    title_tags_trf_df.write_parquet(CH_RECO_TRANSFORMER_DATA_PATH)
