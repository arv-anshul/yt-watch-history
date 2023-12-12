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

from api._utils import batch_iter
from api.configs import API_HOST_URL
from api.models.youtube import YtChannelVideoData
from frontend import st_utils
from frontend.configs import YT_API_KEY
from frontend.constants import VIDEO_DETAILS_JSON_PATH

st.set_page_config("Advance Insights", "😃", "wide", "expanded")
DETAILS_ABOUT_PAGE = """
This app uses **YouTube Data v3 API** to fetch the details of the videos from your
history data. Also it only fetches data of those **videos which you have watched in last
100 days** and only of **those channels which you watched frequently**.

In your case, we will be fetching details of **:green[{len_of_ids} videos]** and using only these
videos details we will give you some insights about your watch time on YouTube.
There are **no YouTube shorts video** data being fetched by the API.

> 👀 Also, Keep in mind that we manage a database of videos details and we filter out those
videoIds which are already available in our database.
"""

# User history dataframe
df = st_utils.get_ingested_yt_history_df()
total_ids = st_utils.get_frequent_ids(df, 100)
total_ids_count = len(total_ids)


# --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- #
def set_status_as_error(__r: httpx.Response, /) -> typing.NoReturn:
    try:
        message = __r.json()["detail"]["message"]
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
    headers: typing.Optional[dict] = None,
    json: typing.Any = None,
) -> typing.Optional[typing.Any]:
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
    if video_details is None:
        status.write("❌ **:red[No video details found in database (in the end).]**")
        status.update(label="No video details found.", expanded=True, state="error")
        st.stop()
    with open(VIDEO_DETAILS_JSON_PATH, "w") as f:
        json.dump(video_details, f, indent=2)


# --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- #
# When videos details not available in local.
# --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- #
if not VIDEO_DETAILS_JSON_PATH.exists():
    with st.expander("🤔 Details About Page"):
        st.write(__doc__)
        st.divider()
        st.markdown(DETAILS_ABOUT_PAGE.format(len_of_ids=total_ids_count))

    with st.form("store-api-key"):
        api_key = st.text_input(
            "Enter YouTube API Key",
            YT_API_KEY if YT_API_KEY else "",
            type="password",
            placeholder="YouTube Data API Key",
        )
        fetch_n_videos = st.number_input(
            "No. of videos details fetch using YouTube API",
            min_value=int(total_ids_count * 0.7) + 1,
            max_value=total_ids_count,
            value=total_ids_count,
            format="%d",
            help="You must have to fetch 70% of videos details of the total videos.",
        )
        if not st.form_submit_button(use_container_width=True):
            st.stop()

    status = st.status("Fetching Data using API key...", expanded=True)
    client = httpx.Client(timeout=22)

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
    if not filtered_ids:
        status.write(":red[No videoIds to fetch.]")
        __finally_get_video_details(client, total_ids)
        st.rerun()

    # Fetch videos details using ids (which are not present in database)
    status.write(f"Fetching {len(filtered_ids)} video details from API.")
    videos_details = []
    __nums = np.linspace(0, 1, (len(filtered_ids) // 200) + 1)
    __pbar = status.empty()
    for i, batch in enumerate(batch_iter(filtered_ids, 200)):
        __pbar.progress(
            __nums[i], ":blue[Fecting videos details using YouTube API in batches.]"
        )
        __details = __request(
            client,
            method="POST",
            url=f"{API_HOST_URL}/yt/video/?n=200",
            json=batch,
            headers={"YT-API-KEY": api_key},
        )
        if __details:
            videos_details.extend(__details)
    __pbar.empty()

    if not videos_details:
        status.write(":red[No video details returned from YouTube API.]")
        __finally_get_video_details(client, total_ids)
        st.rerun()
    status.write(f"Fetched {len(videos_details)} video details from API.")

    # Store videos data into database
    status.write(":orange[Preparing to store fetched data into database.]")
    status.write(":green[Connecting to database...]")
    __nums = np.linspace(0, 1, (len(videos_details) // 100) + 1)
    __pbar = status.empty()
    for i, batch in enumerate(batch_iter(videos_details, 100)):
        __pbar.progress(
            __nums[i], ":blue[Storing details in a batch of 100 into database.]"
        )
        __request(
            client, method="PUT", url=f"{API_HOST_URL}/db/yt/video/bulk", json=batch
        )
    __pbar.empty()
    status.write(":blue[All Details stored in database.]")

    # Store channel videos data into database
    __request(
        client,
        method="PUT",
        url=f"{API_HOST_URL}/db/yt/channel/video/bulk/videosDetails",
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

    if st.button("Refresh Page", type="primary", use_container_width=True):
        st.rerun()
    st.stop()

# --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- #
# Advance Insights from data
# --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- #
# Button to delete all the user's data
st_utils.delete_user_data_button()

st.info("Cooking some insights for you with ❤️.", icon="🧑‍🍳")
