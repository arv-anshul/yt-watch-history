import polars as pl


def validate_data(data: pl.DataFrame) -> pl.DataFrame:
    """
    Validation setp just perform validation on the dataset and do nothing on it.
    """
    req_cols = {"channelId", "channelTitle", "title", "tags"}
    if not all(i in data.columns for i in req_cols):
        raise pl.ColumnNotFoundError(
            "data must contains columns %s" % list(req_cols - set(data.columns))
        )
    return data


def clean_data(data: pl.DataFrame) -> pl.DataFrame:
    """Preform cleaning steps on the dataset."""
    data = (
        data.explode("tags")
        .group_by("channelId", "channelTitle")
        .agg(pl.col("tags", "title").unique())
        .with_columns(pl.col("tags", "title").list.join(" "))
        .filter(
            # Remove those channels which have no tags
            pl.col("tags").ne("null"),
        )
    )
    return data


def preprocess_data(data: pl.DataFrame) -> pl.DataFrame:
    """
    Do all the preprocessing steps like validation, cleaning and more on the dataset.
    """
    data = validate_data(data)
    data = clean_data(data)
    return data
