from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING

import dill
import polars as pl
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ml.channel_reco.configs import (
    CHANNEL_RECO_CHANNELS_DATA_PATH,
    CHANNEL_RECO_TRANSFORMER_PATH,
)

if TYPE_CHECKING:
    from sklearn.pipeline import Pipeline

router = APIRouter(prefix="/channel_reco", tags=["channel_reco"])


@lru_cache(1)
def load_model_from_path() -> tuple[Pipeline, pl.DataFrame]:
    if not CHANNEL_RECO_TRANSFORMER_PATH.exists():
        raise HTTPException(404, {"error": "ChannelReco model not found."})
    with CHANNEL_RECO_TRANSFORMER_PATH.open("rb") as f:
        return dill.load(f), pl.read_parquet(CHANNEL_RECO_CHANNELS_DATA_PATH)


@router.get(
    "/channels",
    description="Get list of channels which were used for training.",
)
def get_channels_list(
    model_data: tuple[Pipeline, pl.DataFrame] = Depends(load_model_from_path),
):
    return model_data[1]


class ChannelRecoIn(BaseModel):
    title: str
    tags: str
    channelId: str
    channelTitle: str


@router.post(
    "/predict",
    description="Make prediction using list of JSON data.",
)
async def predict_many(
    data: list[ChannelRecoIn],
    channels: bool = False,
    model_data: tuple[Pipeline, pl.DataFrame] = Depends(load_model_from_path),
):
    df = pl.DataFrame([i.model_dump() for i in data])
    if df.group_by("channelId", "channelTitle").count().height != 1:
        raise HTTPException(400, {"error": "All channels must be same."})

    similarity = model_data[0].transform(df)
    if channels:
        return (
            model_data[1]
            .with_columns(pl.lit(similarity.ravel()).alias("similarity"))
            .to_dicts()
        )
    return list(similarity.ravel())
