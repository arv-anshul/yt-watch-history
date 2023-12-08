import typing
from datetime import timedelta

import polars as pl
import streamlit as st

import frontend.constants as C
from frontend.youtube import IngestYtHistory

UPLOAD_DATASET_URL = "/YT_History_Basic"

_TimeFreqStr = typing.Literal["weekday", "hour", "month", "year"]


@st.cache_resource
def get_ingested_yt_history_df() -> pl.DataFrame:
    if C.INGESTED_YT_HISTORY_DATA_PATH.exists():
        return IngestYtHistory.from_ingested_data(C.INGESTED_YT_HISTORY_DATA_PATH)
    else:
        st.error("Upload dataset first.", icon="✋")
        st.link_button(
            "Upload Dataset",
            UPLOAD_DATASET_URL,
            type="primary",
            use_container_width=True,
        )
        st.stop()


def get_frequent_ids(
    df: pl.DataFrame,
    last_n_days: int = 100,
) -> list[str]:
    delta = df["time"].max() - timedelta(days=last_n_days)  # type: ignore

    df = df.filter(
        pl.col("time") > delta,
        pl.col("isShorts") == False,  # noqa: E712
    )
    freq_channels = (
        df.drop_nulls("channelName")
        .group_by("channelName")
        .count()
        .filter(pl.col("count") > 10)["channelName"]
    )
    freq_ids = (
        df.filter(pl.col("channelName").is_in(freq_channels))["titleUrl"]
        .str.extract(r"be/(.?+)")
        .to_list()
    )
    return freq_ids
