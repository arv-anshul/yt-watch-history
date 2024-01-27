from __future__ import annotations

from typing import TYPE_CHECKING

from sklearn.naive_bayes import MultinomialNB

from .data import CttDataTransformationPipe
from .model import get_model

if TYPE_CHECKING:
    import polars as pl
    from sklearn.pipeline import Pipeline


def training(raw_data: pl.DataFrame) -> Pipeline:
    data = CttDataTransformationPipe.fit_transform(raw_data)
    model = get_model(MultinomialNB(alpha=0.2))
    model.fit(data["title"], data["contentType"])
    return model


if __name__ == "__main__":
    # Demostrate training pipeline working
    from pathlib import Path

    import dill
    import polars as pl

    raw_data = pl.read_json("data/ctt/channels_data.json").join(
        pl.read_json("data/ctt/titles_data.json"), on="channelId"
    )

    print("Training starts...")
    model = training(raw_data)
    with Path("data/ctt_model.dill").open("wb") as f:
        dill.dump(model, f)
