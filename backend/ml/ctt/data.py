"""
These custom transformers are not a good example and good to use.
"""

from __future__ import annotations

from typing import Self

import polars as pl
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import make_pipeline

from .configs import CONTENT_TYPE_TAGS


class DataValidator(TransformerMixin, BaseEstimator):
    def fit(self, X, y=None) -> Self:
        return self

    def transform(self, X: pl.DataFrame, y=None) -> pl.DataFrame:
        req_cols = {"channelId", "contentType", "title"}
        if not all(i in X.columns for i in req_cols):
            raise pl.ColumnNotFoundError(
                "X must contains columns %s" % list(req_cols - set(X.columns))
            )
        return X


class DataCleaner(TransformerMixin, BaseEstimator):
    def fit(self, X, y=None) -> Self:
        return self

    def transform(self, X: pl.DataFrame, y=None) -> pl.DataFrame:
        X = X.with_columns(
            pl.col("contentType").replace(
                CONTENT_TYPE_TAGS, range(len(CONTENT_TYPE_TAGS))
            ),
        )
        return X


class DataCombiner(TransformerMixin, BaseEstimator):
    """Combine all the identical `contentType` titles as one document."""

    def fit(self, X, y=None) -> Self:
        return self

    def transform(self, X: pl.DataFrame, y=None) -> pl.DataFrame:
        X = (
            X.group_by("contentType")
            .agg("title")
            .with_columns(pl.col("title").list.join(" "))
        )
        return X


CttDataTransformationPipe = make_pipeline(
    DataValidator(), DataCleaner(), DataCombiner()
)
