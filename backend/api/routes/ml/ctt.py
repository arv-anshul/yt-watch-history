from __future__ import annotations

import functools
import logging
from pathlib import Path
from typing import TYPE_CHECKING

import polars as pl
from fastapi import APIRouter, Depends, Header, HTTPException, UploadFile
from pydantic import BaseModel, Field

from api.configs import COLLECTION_CTT_CHANNELS, DB_NAME, YT_VIDEO_COLLECTION
from api.models.ctt import ContentTypeEnum
from api.routes.db.connect import get_db_client
from ml.ctt import (
    CONTENT_TYPE_DECODED,
    CTT_TRAINING_DATA_PATH,
    MODEL_PATH_DILL,
    CttTitleModel,
)

if TYPE_CHECKING:
    from sklearn.pipeline import Pipeline

router = APIRouter(prefix="/ctt", tags=["ctt"])


@router.get(
    "/data",
    description="Fetch titles data for CttTitleModel training from database.",
)
async def get_training_data_from_db():
    pipeline = [
        {
            "$lookup": {
                "from": COLLECTION_CTT_CHANNELS,
                "localField": "channelId",
                "foreignField": "channelId",
                "as": "joinedObj",
            },
        },
        {
            "$unwind": {
                "path": "$joinedObj",
            },
        },
        {
            "$project": {
                "_id": 0,
                "channelId": 1,
                "contentType": "$joinedObj.contentType",
                "title": 1,
            },
        },
    ]
    collection = get_db_client()[DB_NAME][YT_VIDEO_COLLECTION]
    data = collection.aggregate(pipeline).to_list(None)
    return await data


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


class ModelTrainingDataConfig(BaseModel):
    fetch: bool = False
    overwrite: bool = False
    timeoutToFetchData: int = 10


class ModelsParams(BaseModel):
    modelAlpha: float = Field(default=0.01, gt=0)
    tfidfMaxFeatures: int = Field(default=7000, gt=2000)
    tfidfNgramRange: tuple[int, int] = (1, 1)


class ModelTrainingConfig(BaseModel):
    logWithMLFlow: bool = False
    overwrite: bool = False


class ModelTrainingIn(BaseModel):
    modelTrainingConfig: ModelTrainingConfig
    modelParams: ModelsParams
    trainingDataConfig: ModelTrainingDataConfig


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
    # TODO: 1a. Accept MLFlow URI from header or post data (if log is True)
) -> ModelTrainingOut:
    if data.modelTrainingConfig.overwrite is False and MODEL_PATH_DILL.exists():
        raise HTTPException(400, {"error": "Model already exists at path."})
    if data.trainingDataConfig.fetch:
        if data.trainingDataConfig.overwrite:
            CTT_TRAINING_DATA_PATH.unlink(True)
        CttTitleModel.fetch_training_data_from_db(
            timeout=data.trainingDataConfig.timeoutToFetchData
        )

    ctt_obj = CttTitleModel(
        model_alpha=data.modelParams.modelAlpha,
        tfidf_max_features=data.modelParams.tfidfMaxFeatures,
        tfidf_ngram_range=data.modelParams.tfidfNgramRange,
    )

    train_df = ctt_obj.get_df
    train_df = ctt_obj.preprocess_df(train_df)
    if data.modelTrainingConfig.logWithMLFlow:
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
        isModelLogged=data.modelTrainingConfig.logWithMLFlow,
    )
