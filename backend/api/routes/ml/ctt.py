from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING

import dill
import polars as pl
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api.models.ctt import ContentTypeEnum
from ml.ctt.configs import CONTENT_TYPE_TAGS, CTT_MODEL_PATH

if TYPE_CHECKING:
    from sklearn.pipeline import Pipeline

router = APIRouter(prefix="/ctt", tags=["ctt"])


@lru_cache(1)
def load_model_from_path() -> Pipeline:
    if not CTT_MODEL_PATH.exists():
        raise HTTPException(404, {"error": "Ctt Model not found."})
    with CTT_MODEL_PATH.open("rb") as f:
        return dill.load(f)


class PredictionIn(BaseModel):
    title: str
    videoId: str


class PredictionOut(PredictionIn):
    contentTypePred: ContentTypeEnum


@router.post(
    "/predict",
    description="Make prediction using list of JSON data.",
    response_model=list[PredictionOut],
)
async def predict(
    data: list[PredictionIn],
    model: Pipeline = Depends(load_model_from_path),
):
    df = pl.DataFrame([i.model_dump() for i in data])
    prediction = model.predict(df["title"])
    return df.with_columns(
        pl.lit(prediction)
        .map_dict(dict(enumerate(CONTENT_TYPE_TAGS)))
        .alias("contentTypePred")
    ).to_dicts()
