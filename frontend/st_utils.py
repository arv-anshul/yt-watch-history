from __future__ import annotations

from datetime import timedelta
from typing import Literal

import polars as pl
import streamlit as st

from configs import INGESTED_YT_HISTORY_DATA_PATH, VIDEO_DETAILS_JSON_PATH
from youtube import IngestYtHistory

UPLOAD_DATASET_URL = "/YT_History_Basic"

_TimeFreqStr = Literal["weekday", "hour", "month", "year"]


@st.cache_resource
def get_ingested_yt_history_df() -> pl.DataFrame:
    if INGESTED_YT_HISTORY_DATA_PATH.exists():
        return IngestYtHistory.from_ingested_data()
    else:
        st.error("Upload dataset first.", icon="✋")
        st.link_button(
            "Upload Dataset",
            UPLOAD_DATASET_URL,
            type="primary",
            use_container_width=True,
        )
        st.stop()


def get_frequent_ids(df: pl.DataFrame, *, last_n_days: int) -> list[str]:
    delta = df["time"].max() - timedelta(days=last_n_days)  # type: ignore

    df = df.filter(
        pl.col("time") > delta,
        pl.all_horizontal(
            "isShorts", "fromYtSearchHistActivity", "fromWebAppActivity"
        ).eq(False),
    )
    freq_channels = (
        df.drop_nulls("channelTitle")
        .group_by("channelTitle")
        .count()
        .filter(pl.col("count") > 10)["channelTitle"]
    )
    freq_ids = (
        df.filter(pl.col("channelTitle").is_in(freq_channels))["videoId"]
        .unique()
        .to_list()
    )
    return freq_ids


def delete_user_data_button():
    if st.sidebar.button("🗂️ Delete User Data", use_container_width=True):
        all_user_data_paths = (
            INGESTED_YT_HISTORY_DATA_PATH,
            VIDEO_DETAILS_JSON_PATH,
        )
        [i.unlink() for i in all_user_data_paths if i.exists()]

        # Clear streamlit's caches
        st.cache_resource.clear()
        st.cache_data.clear()

        # Rerun the app
        st.rerun()
