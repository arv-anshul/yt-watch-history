import functools

import polars as pl
from fastapi import APIRouter, Depends, Header, HTTPException, UploadFile
from pydantic import BaseModel
from sklearn.pipeline import Pipeline

from backend.api.models.ctt import ContentTypeEnum
from backend.ml.ctt import CONTENT_TYPE_DECODED, CttTitleModel

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
    "/",
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
    "/file",
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
