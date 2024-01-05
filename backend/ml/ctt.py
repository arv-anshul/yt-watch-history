import json
import re
import string
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path

import click
import emoji
import httpx
import mlflow
import mlflow.sklearn
import polars as pl
from mlflow.exceptions import MlflowException
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline

from api.configs import API_HOST_URL
from ml import io

CHANNELS_DATA_PATH = Path("data/ctt/channels_data.json")
TITLES_DATA_PATH = Path("data/ctt/titles_data.json")
MODEL_PATH_MLFLOW = Path("ml_models/ctt_model")
MODEL_PATH_DILL = Path("ml_models/ctt_model.dill")
CONTENT_TYPE_ENCODED = {
    "Education": 1,
    "Entertainment": 2,
    "Movies & Reviews": 3,
    "Music": 4,
    "News": 5,
    "Programming": 6,
    "Pseudo Education": 7,
    "Reaction": 8,
    "Shorts": 9,
    "Tech": 10,
    "Vlogs": 11,
}
CONTENT_TYPE_DECODED = {
    1: "Education",
    2: "Entertainment",
    3: "Movies & Reviews",
    4: "Music",
    5: "News",
    6: "Programming",
    7: "Pseudo Education",
    8: "Reaction",
    9: "Shorts",
    10: "Tech",
    11: "Vlogs",
}


@dataclass(kw_only=True, frozen=True, eq=False)
class CttTitleModel:
    model_alpha: float
    tfidf_max_features: int
    tfidf_ngram_range: tuple[int, int]

    @staticmethod
    def fetch_data_from_database(*, force: bool = False) -> None:
        if CHANNELS_DATA_PATH.exists() and TITLES_DATA_PATH.exists():
            raise FileExistsError(
                f"{CHANNELS_DATA_PATH} and {TITLES_DATA_PATH} already exists."
            )

        error_msg = (
            "Error while fetching data from database. API instance is not running."
        )
        if not CHANNELS_DATA_PATH.exists() or force:
            try:
                response = httpx.post(f"{API_HOST_URL}/db/ctt/")
            except httpx.ConnectError as e:
                raise RuntimeError(error_msg) from e
            with CHANNELS_DATA_PATH.open("w") as f:
                json.dump(response.json(), f)

        if not TITLES_DATA_PATH.exists() or force:
            try:
                # FIXME: Fetch only required columns used for model training from db
                response = httpx.post(f"{API_HOST_URL}/db/yt/video/all")
            except httpx.ConnectError as e:
                raise RuntimeError(error_msg) from e
            with TITLES_DATA_PATH.open("w") as f:
                json.dump(response.json(), f)

    def __post_init__(self) -> None:
        if not CHANNELS_DATA_PATH.exists():
            raise FileNotFoundError(f"'{CHANNELS_DATA_PATH}' not exists.")
        if not TITLES_DATA_PATH.exists():
            raise FileNotFoundError(f"'{TITLES_DATA_PATH}' not exists.")

    @cached_property
    def get_df(self) -> pl.DataFrame:
        ctt_channels_df = pl.read_json(CHANNELS_DATA_PATH)
        titles_df = pl.read_json(TITLES_DATA_PATH)
        self._validate_df(titles_df=titles_df, ctt_channels_df=ctt_channels_df)
        merged_df = titles_df.join(ctt_channels_df, on="channelId").unique("title")
        merged_df = self.preprocess_df(merged_df)
        return merged_df

    def _validate_df(
        self, *, titles_df: pl.DataFrame, ctt_channels_df: pl.DataFrame
    ) -> None:
        titles_df_req_cols = {"channelId", "title"}
        ctt_channels_df_req_cols = {"channelId", "contentType"}
        if not all(i in titles_df.columns for i in titles_df_req_cols):
            raise pl.ColumnNotFoundError(titles_df_req_cols - set(titles_df.columns))
        if not all(i in ctt_channels_df.columns for i in ctt_channels_df_req_cols):
            raise pl.ColumnNotFoundError(
                ctt_channels_df_req_cols - set(ctt_channels_df.columns)
            )

    def preprocess_df(self, df: pl.DataFrame) -> pl.DataFrame:
        df = df.with_columns(
            pl.col("contentType").replace(CONTENT_TYPE_ENCODED),
        )
        return df

    def text_preprocessor(self, s: str):
        """Preprocessor for Vectorizer"""
        s = re.sub(r"\b\w{1,3}\b", " ", s)
        s = s.translate(str.maketrans("", "", string.punctuation + string.digits))
        s = emoji.replace_emoji(s, "")
        s = re.sub(r"\s+", " ", s)
        return s

    def train(self, df: pl.DataFrame) -> Pipeline:
        vectorizer = TfidfVectorizer(
            preprocessor=self.text_preprocessor,
            max_features=self.tfidf_max_features,
            ngram_range=self.tfidf_ngram_range,
            stop_words="english",
        )
        model = Pipeline(
            [
                ("vectorizer", vectorizer),
                ("multinomial", MultinomialNB(alpha=self.model_alpha)),
            ]
        )

        # Modify dataframe to train the model
        df = (
            df.group_by("contentType")
            .agg("title")
            .with_columns(pl.col("title").list.join(" "))
        )
        model.fit(df["title"], df["contentType"])
        return model

    def model_score(self, model: Pipeline, df: pl.DataFrame):
        y_true = df["contentType"]
        y_pred = model.predict(df["title"])

        scores = {
            i.__name__: float(i(y_true, y_pred, average="weighted"))
            for i in (
                f1_score,
                precision_score,
                recall_score,
            )
        }
        scores["accuracy_score"] = float(accuracy_score(y_true, y_pred))
        cm = confusion_matrix(y_true, y_pred).tolist()
        return scores, cm

    def initiate(self, *, save_model: bool) -> None:
        df = self.get_df
        model = self.train(df)

        # Log model params using mlflow
        mlflow.log_params({i: getattr(self, i) for i in self.__annotations__})

        # Log model metrices using mlflow
        scores, cm = self.model_score(model, df)
        mlflow.log_metrics(scores)
        mlflow.log_dict({"confusion_matrix": cm}, "confusion_matrix.json")

        # Log model using mlflow
        mlflow.sklearn.log_model(
            model, MODEL_PATH_MLFLOW.as_posix(), serialization_format="pickle"
        )

        if save_model:
            self.store_model(model)

    @classmethod
    def store_model(cls, model: Pipeline) -> None:
        io.dump_object(model, MODEL_PATH_DILL)

    @classmethod
    def load_model_dill(cls) -> Pipeline:
        if not MODEL_PATH_DILL.exists():
            raise FileNotFoundError(f"Ctt Model not found at {MODEL_PATH_DILL!r}")
        model = io.load_object(MODEL_PATH_DILL)
        return model

    @classmethod
    def load_model_mlflow(cls, run_id: str) -> Pipeline:
        logged_model_path = f"runs:/{run_id}/"
        model = mlflow.sklearn.load_model(logged_model_path / MODEL_PATH_MLFLOW)
        if model is None:
            raise MlflowException("Error while loading model with mlflow.")
        return model


@click.command(
    help="Train CttTitleModel",
)
@click.option(
    "--model-alpha",
    default=0.01,
    type=float,
    help="Alpha value for Multinomial Naive Bayes model.",
)
@click.option(
    "--tfidf-max-features",
    default=7_000,
    type=int,
    help="Maximum number of features for TF-IDF vectorization.",
)
@click.option(
    "--tfidf-ngram-range",
    default="1:1",
    type=click.Choice(["1:1", "1:2", "1:3", "2:2"]),
    help="Ngram range for TF-IDF vectorization. Pass value as '1:2' to parse as (1, 2).",
    show_default=True,
)
@click.option(
    "--save-model",
    is_flag=True,
    help="Flag to save ML model using mlflow.",
)
def pipeline_for_ctt_model(
    model_alpha: float,
    tfidf_max_features: int,
    tfidf_ngram_range: str,
    save_model: bool,
):
    ctt_title = CttTitleModel(
        model_alpha=model_alpha,
        tfidf_max_features=tfidf_max_features,
        tfidf_ngram_range=tuple(map(int, tfidf_ngram_range.split(":"))),  # type: ignore
    )

    with mlflow.start_run():
        ctt_title.initiate(save_model=save_model)


if __name__ == "__main__":
    pipeline_for_ctt_model()
