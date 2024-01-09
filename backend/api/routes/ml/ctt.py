from __future__ import annotations

import functools
import logging
from pathlib import Path
from typing import TYPE_CHECKING

import polars as pl
from fastapi import APIRouter, Depends, Header, HTTPException, UploadFile
from pydantic import BaseModel, Field

from api.models.ctt import ContentTypeEnum
from ml.ctt import (
    CHANNELS_DATA_PATH,
    CONTENT_TYPE_DECODED,
    MODEL_PATH_DILL,
    TITLES_DATA_PATH,
    CttTitleModel,
)

if TYPE_CHECKING:
    from sklearn.pipeline import Pipeline

router = APIRouter(prefix="/ctt", tags=["ctt"])


class PredictionIn(BaseModel):
    title: str
    videoId: str


class PredictionOut(PredictionIn):
    contentTypePred: ContentTypeEnum


@functools.lru_cache(1)
def load_model(
    run_id: str | None = Header(None, alias="X-MLFLOW-RUN-ID"),
) -> Pipeline:
    if run_id:
        print("Loading Models from mlflow...")
        model = CttTitleModel.load_model_mlflow(run_id)
    else:
        try:
            model = CttTitleModel.load_model_dill()
        except FileNotFoundError as e:
            raise HTTPException(404, {"error": str(e)}) from e
    return model


def predict_with_df(*, df: pl.DataFrame, model: Pipeline) -> pl.DataFrame:
    prediction = model.predict(df["title"])
    df = df.with_columns(
        pl.lit(prediction).map_dict(CONTENT_TYPE_DECODED).alias("contentTypePred"),
    )
    return df


@router.post(
    "/predict",
    description="Make prediction using list of JSON data.",
    response_model=list[PredictionOut],
)
async def predict_many(
    data: list[PredictionIn],
    model: Pipeline = Depends(load_model),
):
    df = pl.DataFrame([i.model_dump() for i in data])
    df = predict_with_df(df=df, model=model)
    return df.to_dicts()


@router.post(
    "/predict/file",
    description="Make prediction using JSON file.",
    response_description="Download the JSON file which includes the predicted contentType.",
)
async def predict_with_file(
    file: UploadFile,
    model: Pipeline = Depends(load_model),
):
    df = pl.read_json(file.file.read())
    df = predict_with_df(df=df, model=model)
    return df.to_dicts()


@router.post(
    "/store-logged-model",
    description="Store Ctt ML Model which had been logged using mlflow.",
)
async def store_logged_model(
    run_id: str = Header(alias="X-MLFLOW-RUN-ID"),
) -> None:
    model = CttTitleModel.load_model_mlflow(run_id)
    CttTitleModel.store_model(model)


@router.get(
    "/fetchTrainingDataFromDb",
    description=(
        "Fetches data for CttTitleModel training from database. It will save data at "
        "the specified path."
    ),
)
async def fetch_data_for_training(
    force: bool = False,
):
    CttTitleModel.fetch_data_from_database(force=force)
    return {
        "channelsDataPath": CHANNELS_DATA_PATH.as_uri(),
        "titlesDataPath": TITLES_DATA_PATH.as_uri(),
    }


class ModelsParams(BaseModel):
    modelAlpha: float = Field(default=0.01, gt=0)
    tfidfMaxFeatures: int = Field(default=7000, gt=2000)
    tfidfNgramRange: tuple[int, int] = (1, 1)


class ModelTrainingIn(BaseModel):
    modelParams: ModelsParams


class ModelTrainingOut(BaseModel):
    scores: dict[str, float]
    isModelLogged: bool
    modelPath: Path
    # TODO: 1b. Add MLFlow tracking URI link
    confusion_matrix: list[list[int]]


@router.post(
    "/train",
    description=(
        "Train Ctt model using video titles data. This may takes few seconds to "
        "response."
    ),
)
async def train_ctt_model(
    data: ModelTrainingIn,
    overwrite: bool = False,
    log: bool = False,
    # TODO: 1a. Accept MLFlow URI from header or post data (if log is True)
) -> ModelTrainingOut:
    if overwrite is False and MODEL_PATH_DILL.exists():
        raise HTTPException(400, {"error": "Model already exists at path."})

    ctt_obj = CttTitleModel(
        model_alpha=data.modelParams.modelAlpha,
        tfidf_max_features=data.modelParams.tfidfMaxFeatures,
        tfidf_ngram_range=data.modelParams.tfidfNgramRange,
    )

    train_df = ctt_obj.get_df
    train_df = ctt_obj.preprocess_df(train_df)
    if log:
        ctt_obj.initiate(save_model=True)
        model = ctt_obj.load_model_dill()
    else:
        model = ctt_obj.train(train_df)

    scores, cm = ctt_obj.model_score(model, train_df)
    logging.critical(f"CttTitleModel scores: {scores}")

    logging.info(f"Storing model at {MODEL_PATH_DILL.resolve(True)}.")
    CttTitleModel.store_model(model)

    return ModelTrainingOut(
        scores=scores,
        confusion_matrix=cm,
        modelPath=MODEL_PATH_DILL.resolve(True),
        isModelLogged=log,
    )
