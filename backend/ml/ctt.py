import json
import os
import re
import string
from dataclasses import dataclass
from functools import cached_property

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

from backend.api.configs import API_HOST_URL
from backend.ml import io

CHANNELS_DATA_PATH = "data/ctt/channels_data.json"
TITLES_DATA_PATH = "data/ctt/titles_data.json"
MODEL_PATH = "ml_models/ctt_model"
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
    ctt_channels_data: str
    titles_data: str
    model_alpha: float
    tfidf_max_features: int
    tfidf_ngram_range: tuple[int, int]
    save_model: bool

    def __fetch_data_from_database(self) -> None:
        if (
            not os.path.exists(CHANNELS_DATA_PATH)
            and self.ctt_channels_data == CHANNELS_DATA_PATH
        ):
            try:
                data = httpx.post(f"{API_HOST_URL}/db/ctt/")
            except httpx.HTTPError:
                raise RuntimeError(
                    f"Data not present on path {CHANNELS_DATA_PATH!r} and "
                    f"{TITLES_DATA_PATH!r}. Error while fetching data from database. "
                    "API instance is not running."
                )
            with open(CHANNELS_DATA_PATH, "w") as f:
                json.dump(data, f)
        if (
            not os.path.exists(TITLES_DATA_PATH)
            and self.titles_data == TITLES_DATA_PATH
        ):
            data = httpx.post(f"{API_HOST_URL}/db/yt/video/all")
            with open(TITLES_DATA_PATH, "w") as f:
                json.dump(data, f)

    @cached_property
    def get_df(self) -> pl.DataFrame:
        ctt_channels_df = pl.read_json(self.ctt_channels_data)
        titles_df = pl.read_json(self.titles_data)
        self._validate_df(titles_df=titles_df, ctt_channels_df=ctt_channels_df)
        return titles_df.join(ctt_channels_df, on="channelId").unique("title")

    def _validate_df(
        self, *, titles_df: pl.DataFrame, ctt_channels_df: pl.DataFrame
    ) -> None:
        titles_df_req_cols = {"channelId", "title"}
        ctt_channels_df_req_cols = {"channelId", "contentType"}
        if not all(i in titles_df.columns for i in titles_df_req_cols):
            raise pl.ColumnNotFoundError(titles_df_req_cols - set(titles_df.columns))
        elif not all(i in ctt_channels_df.columns for i in ctt_channels_df_req_cols):
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

    def initiate(self) -> None:
        self.__fetch_data_from_database()
        df = self.get_df
        df = self.preprocess_df(df)
        model = self.train(df)

        # Log model params using mlflow
        mlflow.log_params({i: getattr(self, i) for i in self.__annotations__.keys()})

        # Log model metrices using mlflow
        scores, cm = self.model_score(model, df)
        mlflow.log_metrics(scores)
        mlflow.log_dict({"confusion_matrix": cm}, "confusion_matrix.json")

        # Log model using mlflow
        mlflow.sklearn.log_model(model, MODEL_PATH, serialization_format="pickle")

        if self.save_model:
            self.store_model(model)

    @classmethod
    def store_model(cls, model: Pipeline) -> None:
        io.dump_object(model, MODEL_PATH + ".dill")

    @classmethod
    def load_model_dill(cls) -> Pipeline:
        path = MODEL_PATH + ".dill"
        if not os.path.exists(path):
            raise FileNotFoundError(f"Ctt Model not found at {path!r}")
        (model,) = io.load_objects(path)
        return model

    @classmethod
    def load_model_mlflow(cls, run_id: str) -> Pipeline:
        logged_model_path = f"runs:/{run_id}/"
        model = mlflow.sklearn.load_model(logged_model_path + MODEL_PATH)
        if model is None:
            raise MlflowException("Error while loading model with mlflow.")
        return model


@click.command(
    help="Train CttTitleModel",
)
@click.option(
    "--ctt-channels-data",
    default=CHANNELS_DATA_PATH,
    type=str,
    help="Path to CTT channels data JSON file.",
)
@click.option(
    "--titles-data",
    default=TITLES_DATA_PATH,
    type=str,
    help="Path to titles data JSON file.",
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
    ctt_channels_data: str,
    titles_data: str,
    model_alpha: float,
    tfidf_max_features: int,
    tfidf_ngram_range: str,
    save_model: bool,
):
    ctt_title = CttTitleModel(
        ctt_channels_data=ctt_channels_data,
        titles_data=titles_data,
        model_alpha=model_alpha,
        tfidf_max_features=tfidf_max_features,
        tfidf_ngram_range=tuple(map(int, tfidf_ngram_range.split(":"))),  # type: ignore
        save_model=save_model,
    )

    with mlflow.start_run():
        ctt_title.initiate()


if __name__ == "__main__":
    pipeline_for_ctt_model()
