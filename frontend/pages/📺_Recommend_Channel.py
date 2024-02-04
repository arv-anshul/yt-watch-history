"""
Upload your subscribed channels data (exported from Google Takeout) to get
recommendation of similar channels.
"""

import polars as pl
import streamlit as st

import st_utils
from configs import INGESTED_YT_HISTORY_DATA_PATH, VIDEO_DETAILS_JSON_PATH
from youtube.channel_reco import (
    RecommendChannels,
    add_subscribed_column,
    check_if_subscribed_column_exists,
)

st.set_page_config("Recommend Channel", "😃", "wide", "expanded")
st_msg = st.container()
st_utils.delete_user_data_button()

if not INGESTED_YT_HISTORY_DATA_PATH.exists():
    st.switch_page("/pages/🐻‍❄️_YT_History_Basic.py")
if not VIDEO_DETAILS_JSON_PATH.exists():
    st_msg.error("First collect data of YouTube Videos.", icon="🤖")
    st.stop()
ingested_data = st_utils.get_ingested_yt_history_df()
video_details_data = pl.read_json(VIDEO_DETAILS_JSON_PATH)

try:
    check_if_subscribed_column_exists(ingested_data)
    st.title("Recommend Channels from you Subscribed Channels")
except ValueError:
    uploaded_file = st_msg.file_uploader(
        "Upload your subscribed channels data file. (.csv)", type=".csv"
    )
    if uploaded_file is None:
        st.stop()
    # Update the ingested_data and write into file
    add_subscribed_column(ingested_data, pl.read_csv(uploaded_file)).write_json(
        INGESTED_YT_HISTORY_DATA_PATH
    )
    st.rerun()

try:
    recommendation = RecommendChannels(ingested_data, video_details_data)
except ValueError as e:
    st_msg.error(e)
    st.stop()

sl_channel_title = st.selectbox(
    "Select Channel",
    recommendation.data["channelTitle"].unique().sort().to_list(),
)
if sl_channel_title is None:
    st.stop()

st.dataframe(
    recommendation.get_recommendations(sl_channel_title).sort(
        "similarity", descending=True
    ),
    use_container_width=True,
)
