import polars as pl

from utils import make_request_to_api

from ..configs import CH_RECO_DATA_PATH


def ingest_data_from_db() -> pl.DataFrame:
    """Ingest training data from Database."""
    data = make_request_to_api(method="GET", endpoint="/ml/channelReco/data")
    return pl.read_json(data)


def ingest_data_from_file() -> pl.DataFrame:
    """
    Ingest training data from local file. Path is already specified at
    `data/channel_reco/training.json`.
    """
    if CH_RECO_DATA_PATH.exists():
        return pl.read_json(CH_RECO_DATA_PATH)
    raise FileNotFoundError(f"{CH_RECO_DATA_PATH = }")


def validate_data(df: pl.DataFrame) -> pl.DataFrame:
    """
    Validation setp just perform validation on the dataset and do nothing on it.
    """
    req_cols = {"channelId", "title", "tags"}
    if not all(i in df.columns for i in req_cols):
        raise pl.ColumnNotFoundError(
            "Required columns for Channel Recommender System: "
            f"{req_cols - set(df.columns)}"
        )
    return df


def clean_data(df: pl.DataFrame) -> pl.DataFrame:
    """Preform cleaning steps on the dataset."""
    df = (
        df.explode("tags")
        .group_by("channelId", "channelTitle")
        .agg(pl.col("tags", "title").unique())
        .with_columns(pl.col("tags", "title").list.join(" "))
        .filter(
            # Remove those channels which have no tags
            pl.col("tags").ne("null"),
        )
    )
    return df


def preprocess_data(df: pl.DataFrame) -> pl.DataFrame:
    """
    Do all the preprocessing steps like validation, cleaning and more on the dataset.
    """
    df = validate_data(df)
    df = clean_data(df)
    return df
