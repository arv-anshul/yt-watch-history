"""
##### 🤔 How do our app fetch data and show `📊 Advance Insights` on this page at the same time?
  - Filter out the videoIds from the dataset with the constraints.
  - Exclude the videoIds which are already present the database.
  - Fetch video details from YouTube API using the videoIds which are not available in database.
  - Push those video details into database.
  - Push the Channel's videoIds data into database.
  - Finally, fetch all the videos details using `total_ids` from database and store
    them into a JSON file.
###### 🤩 Now, show the Advance Insights by merging both datasets.
"""

import json
import typing

import httpx
import numpy as np
import polars as pl
import streamlit as st
from plotly import express as px

from backend.api._utils import batch_iter
from backend.api.configs import API_HOST_URL
from backend.api.models.youtube import YtChannelVideoData
from frontend import st_utils
from frontend.configs import VIDEO_DETAILS_JSON_PATH, YT_API_KEY
from frontend.youtube import VideoDetails

st.set_page_config("Advance Insights", "😃", "wide", "expanded")
DETAILS_ABOUT_PAGE = """
This app uses **YouTube Data v3 API** to fetch the details of the videos from your
history data. Also it only fetches data of those **videos which you have watched in last
(n) days** and only of **those channels which you watched frequently**.

We only fetches video details of recently watched videos and using only these
videos details we will give you some insights about your watch time on YouTube.
There are **no YouTube shorts video** data being fetched by the API.

> 👀 Also, Keep in mind that we manage a database of videos details and we filter out those
videoIds which are already available in our database.
"""

# User history dataframe
df = st_utils.get_ingested_yt_history_df()


# --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- #
def set_status_as_error(__r: httpx.Response, /) -> typing.NoReturn:
    try:
        message = __r.json()["error"]
    except json.JSONDecodeError:
        message = __r.text
    except (KeyError, TypeError):
        message = __r.json()
    if isinstance(message, str):
        message = f"❌ **:red[{message}]**"
    status.write(message)
    status.update(label="ERROR OCCURRED!", expanded=False, state="error")
    st.stop()


def __request(
    client: httpx.Client,
    *,
    method: typing.LiteralString,
    url: str,
    headers: dict | None = None,
    json: typing.Any = None,
) -> typing.Any | None:
    try:
        r = client.request(method, url, headers=headers, json=json)
    except httpx.ConnectError:
        status.write("**:red[Check your network and make sure the API is running.]**")
        status.update(
            label="Connection establishment failed.", expanded=False, state="error"
        )
        st.stop()

    if r.status_code == 204:
        return None
    elif r.is_success:
        return r.json()
    set_status_as_error(r)


def __finally_get_video_details(client: httpx.Client, ids: list[str]) -> None:
    status.write(":green[Finally fetching all videos details.]")
    video_details = __request(
        client, method="POST", url=f"{API_HOST_URL}/db/yt/video/", json=ids
    )
    if not video_details:
        status.write("❌ **:red[No video details found in database (in the end).]**")
        status.update(label="No video details found.", expanded=True, state="error")
        st.stop()
    with VIDEO_DETAILS_JSON_PATH.open("w") as f:
        json.dump(video_details, f)


# --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- #
# When videos details not available in local.
# --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- #
if not VIDEO_DETAILS_JSON_PATH.exists():
    with st.expander("🤔 Details About Page"):
        st.write(__doc__)
        st.divider()
        st.markdown(DETAILS_ABOUT_PAGE)

    with st.form("store-api-key"):
        api_key = st.text_input(
            "Enter YouTube API Key",
            YT_API_KEY if YT_API_KEY else "",
            type="password",
            placeholder="YouTube Data API Key",
        )
        last_n_days = st.number_input(
            "Fetch Data of Last (n) Days", 300, 500, "min", 20, "%d"
        )
        if not st.form_submit_button(use_container_width=True):
            st.stop()

    total_ids = st_utils.get_frequent_ids(df, last_n_days=int(last_n_days))
    total_ids_count = len(total_ids)  # Store count of total ids
    status = st.status("Fetching Data using API key...", expanded=True)
    client = httpx.Client(timeout=10)

    # excludeVideoIds which are present in database
    filtered_ids = __request(
        client,
        method="POST",
        url=f"{API_HOST_URL}/db/yt/channel/video/excludeExistingIds",
        json=[
            i.model_dump()
            for i in YtChannelVideoData.from_df(
                df.filter(pl.col("videoId").is_in(total_ids))
            )
        ],
    )

    # When all ids present in database
    if not filtered_ids:
        status.write(":red[No videoIds to fetch.]")
        __finally_get_video_details(client, total_ids)
        st.rerun()

    # Fetch videos details using ids (which are not present in database)
    status.write(f"Fetching {len(filtered_ids)} video details from API.")
    videos_details = []
    __nums = np.linspace(0, 1, (len(filtered_ids) // 400) + 1)
    __pbar = status.empty()
    for i, batch in enumerate(batch_iter(filtered_ids, 400)):
        __pbar.progress(
            __nums[i], ":blue[Fecting videos details using YouTube API in batches.]"
        )
        v = __request(
            client,
            method="POST",
            url=f"{API_HOST_URL}/yt/video/?n=400",
            json=batch,
            headers={"YT-API-KEY": api_key},
        )
        if v:
            videos_details.extend(v)
    else:
        __pbar.empty()

    # When no videos details returned by youtube's api
    if not videos_details:
        status.write(":red[No video details returned from YouTube API.]")
        __finally_get_video_details(client, total_ids)
        st.rerun()
    status.write(f"Fetched {len(videos_details)} video details from API.")

    # Store videos data into database
    status.write(":orange[Preparing to store fetched data into database.]")
    status.write(":green[Connecting to database...]")
    __nums = np.linspace(0, 1, (len(videos_details) // 200) + 1)
    __pbar = status.empty()
    for i, batch in enumerate(batch_iter(videos_details, 200)):
        __pbar.progress(
            __nums[i], ":blue[Storing details in a batch of 200 into database.]"
        )
        __request(client, method="PUT", url=f"{API_HOST_URL}/db/yt/video/", json=batch)
    else:
        __pbar.empty()
    status.write(":blue[All Details stored in database.]")

    # Store channel videos data into database
    __request(
        client,
        method="PUT",
        url=f"{API_HOST_URL}/db/yt/channel/video/usingVideosDetails",
        json=videos_details,
    )
    status.write("Channel videos data stored in database.")

    # Finally fetch videos details from database
    __finally_get_video_details(client, total_ids)
    status.update(
        label=":green[Pulling from API and Pushing into database completed.]",
        expanded=False,
        state="complete",
    )

    # Close httpx client
    client.close()

    # Refresh button
    if st.button("Refresh Page", type="primary", use_container_width=True):
        st.rerun()
    st.stop()

# --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- #
# Advance Insights from data
# --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- #
# Button to delete all the user's data
st_utils.delete_user_data_button()

mdf = VideoDetails().initiate()

_options = (
    "Basic Insights",
    "User's Watchtime Behavior Analysis",
    "User's Behavior on Videos Duration",
)
sl_analysis = st.selectbox("Select Analysis", options=_options)
sl_year = st.selectbox(
    "Select Year",
    [None, *mdf["year"].unique().sort(descending=True).to_list()],
)
l, r = st.columns(2)

# Filtered DataFrame
mdf = mdf.filter(pl.col("year") == sl_year) if sl_year else mdf

# --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- #
# Basic Analysis
# --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- #
if sl_analysis == _options[0]:
    fig = px.sunburst(
        mdf.group_by(["channelTitle", "categoryName"]).count(),
        path=["categoryName", "channelTitle"],
        values="count",
        title="Video Distribution by Category and Channel",
    )
    l.plotly_chart(fig, True)

# --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- #
# Watchtime Behavior
# --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- #
if sl_analysis == _options[1]:
    fig = px.sunburst(
        mdf.group_by(["daytime", "categoryName"]).count(),
        path=["daytime", "categoryName"],
        values="count",
        title="User's watching behavior during daytime",
    )
    l.plotly_chart(fig, True)

    fig = px.sunburst(
        mdf.group_by(["month", "categoryName"]).count(),
        path=["month", "categoryName"],
        values="count",
        title="Watching patterns for months.",
    )
    r.plotly_chart(fig, True)

# --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- #
# Videos Duration Behavior
# --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- #
if sl_analysis == _options[2]:
    fig = px.pie(
        mdf["isShorts"]
        .map_elements(lambda x: "Shorts Video" if x else "Long Videos")
        .value_counts(),
        names="isShorts",
        values="count",
        title="Ratio between Shorts and Long Form Video",
    )
    l.plotly_chart(fig, True)

    fig = px.sunburst(
        mdf.group_by("categoryName", "channelTitle").agg(
            pl.col("durationInSec").mean().cast(int).alias("durationMean"),
        ),
        path=["categoryName", "channelTitle"],
        values="durationMean",
        title="Average Video Duration by Category and Channel",
    )
    r.plotly_chart(fig, True)

    fig = px.sunburst(
        mdf.group_by("categoryName", "channelTitle").agg(
            pl.col("isShorts").sum(),
        ),
        path=["categoryName", "channelTitle"],
        values="isShorts",
        title="Distribution of Shorts by Channels",
    )
    l.plotly_chart(fig, True)
