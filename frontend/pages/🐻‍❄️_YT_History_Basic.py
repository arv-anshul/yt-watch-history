import calendar

import httpx
import polars as pl
import streamlit as st
from matplotlib import pyplot as plt
from plotly import express as px
from polars import selectors as cs
from wordcloud import STOPWORDS, WordCloud

import st_utils
from configs import API_HOST_URL, INGESTED_YT_HISTORY_DATA_PATH
from youtube import IngestYtHistory

st.set_page_config("YT Watch History", "🐻‍❄", "wide")
df = None

# Import or Upload data into app
if INGESTED_YT_HISTORY_DATA_PATH.exists():
    df = st_utils.get_ingested_yt_history_df()
else:
    with st.form("upload-yt-history-data"):
        df_buffer = st.file_uploader("Upload dataset (.json)", type=".json")
        if not st.form_submit_button(use_container_width=True):
            st.stop()
        if df_buffer is None:
            st.error(
                "Error while uploading the file. Upload JSON file properly.",
                icon="🧐",
            )
            st.stop()
        else:
            INGESTED_YT_HISTORY_DATA_PATH.write_bytes(df_buffer.read())

    with st.status("Loading the data into app...", expanded=True) as status:
        df = IngestYtHistory().initiate()
        status.write(":green[👍 Data has been loaded.]")

        # Predict the videos ContentType
        status.write(":orange[🤔 Predicting the videos ContentType.]")
        try:
            response = httpx.post(
                f"{API_HOST_URL}/ml/ctt/",
                json=df.select("title", "videoId").to_dicts(),
            )
        except httpx.ConnectError:
            status.update(
                label="API instance not running", expanded=False, state="error"
            )
            st.stop()
        if not response.is_success:
            status.update(
                label="Model not present at path", expanded=False, state="error"
            )
            st.stop()

        pred_df = pl.DataFrame(response.json())
        status.write(":green[🎊 Prediction compleated!]")
        df = df.join(pred_df, on="videoId").drop(cs.ends_with("_right"))
        df.write_json(INGESTED_YT_HISTORY_DATA_PATH, row_oriented=True)
        status.update(
            label="📦 Stored ingested data as JSON.", expanded=False, state="complete"
        )

    if st.button("Refresh The Page", type="primary", use_container_width=True):
        st.rerun()
    st.stop()

# Button to delete all the user's data
st_utils.delete_user_data_button()
CAPTION = st.sidebar.toggle("Plots Caption", True)

_options = [
    "Basic Info About Your History Data",
    "Watch Time Insights",
    "Video Titles' Keywords' WordCloud",
    "ContentType Models Overview",
]
sl_analysis = st.selectbox("Select Which Type Of Analysis You Want To See 👀", _options)

# --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- #
# Basic Insights
# --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- #
if sl_analysis == _options[0]:
    l, r = st.columns(2)

    # Dataset time range
    l.metric(
        "Time Range of Dataset",
        f'{df["time"].min():%b, %y} — {df["time"].max():%b, %y}',
    )
    r.metric("No. of Days of Data Present", df["time"].dt.date().n_unique())

    # No. Of Channels You Watches Frequently
    threshold = 7
    fig = px.pie(
        values=df["channelTitle"]
        .value_counts()
        .select(
            pl.col("count").ge(7).sum().alias("ge"),
            pl.col("count").is_between(2, 6).sum().alias("lt"),
        )
        .row(0),
        names=["Frequently Watched Channel (>=7)", "Non Freq. Channel [2,6]"],
        title=f"% of channels you watches frequently [{threshold=}]",
    )
    l.plotly_chart(fig, True)

    # Count Of Video Watched From Different Activity
    temp = df.select(
        "fromYtSearchHistActivity", "fromYtWatchHistActivity", "fromWebAppActivity"
    ).sum()
    fig = px.pie(
        values=temp.row(0),
        names=temp.columns,
        title="Count of videos you have watched from different activity",
    )
    r.plotly_chart(fig, True)

    # Top 7 Channel
    fig = px.bar(
        df["channelTitle"].value_counts(sort=True).head(7),
        "channelTitle",
        "count",
        title="Top 7 channels you have watched",
    )
    st.plotly_chart(fig, True)


# --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- #
# Watch Time Insights
# --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- #
if sl_analysis == _options[1]:
    st.divider()

    L, R = st.columns(2)
    sl_year = L.selectbox(
        "Select Year",
        [None, *df["time"].dt.year().unique().sort()],
        format_func=lambda x: x if x else "All",
    )
    sl_month = R.selectbox(
        "Select Month",
        [None, *range(1, 13)],
        format_func=lambda x: calendar.month_name[x] if x else "All",
    )
    st.divider()

    filter_queries = []
    if sl_year:
        filter_queries.append(pl.col("time").dt.year().eq(sl_year))
    if sl_month:
        filter_queries.append(pl.col("time").dt.month().eq(sl_month))
    if not filter_queries:
        filter_queries.append(True)

    fig = px.bar(
        (
            df.filter(filter_queries)
            .group_by("contentTypePred", "daytime")
            .count()
            .sort("count", descending=True)
        ),
        x="contentTypePred",
        y="count",
        color="daytime",
        labels={"contentTypePred": "Videos Content Type", "count": "Video Count"},
        title="Count of videos watched in each Content Type (Stacked with daytime)",
    )
    st.plotly_chart(fig, True)
    if CAPTION:
        st.caption(
            "A grouped bar chart showcasing the top video content types, while "
            "color-coded by time of day. Reveals the most prevalent content types "
            "across different times, offering insights into popular video categories "
            "and their distribution throughout the day."
        )
    st.divider()

    L, R = st.columns(2)
    fig = px.sunburst(
        (
            df.filter(filter_queries)
            .group_by("contentTypePred", "daytime", "channelTitle")
            .count()
            .filter(pl.col("count").gt(20 if not sl_month else 1))
        ),
        path=["contentTypePred", "channelTitle", "daytime"],
        values="count",
        title="User's watching behavior during contentTypePred",
    )
    L.plotly_chart(fig, True)
    if CAPTION:
        L.caption(
            "Sunburst chart displaying significant content type distribution across "
            "channels and time of day, highlighting content types , providing insights "
            "into popular content categories, channel engagement, and viewing patterns "
            "throughout the day. Constraints with (count > 20)."
        )


# --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- #
# WordCloud from Videos Title
# --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- #
@st.cache_resource
def generate_cloud():
    title = df.filter(
        pl.col("isShorts").eq(False),
    )
    text: str = (
        title["title"]
        .str.replace_all(r"\b\w{1,3}\b", " ")
        .str.replace_all(r"\s+", " ")
        .implode()
        .list.join(" ")
        .item()
    )
    cloud = WordCloud(width=800, height=800, stopwords=STOPWORDS).generate(text)
    return cloud


if sl_analysis == _options[2]:
    fig = plt.figure(figsize=(10, 10), facecolor=None)
    plt.imshow(generate_cloud())
    plt.axis("off")
    plt.title("WorlCloud of Words in Videos Title")
    st.pyplot(fig, True)

    # WordCloud of titleTags
    tags_text = " ".join(
        df["titleTags"]
        .explode()
        .drop_nulls()
        .str.strip_prefix("#")
        .str.to_lowercase()
        .to_list()
    )
    cloud = WordCloud(height=800, width=800).generate(tags_text)
    fig = plt.figure(figsize=(10, 10), facecolor=None)
    plt.imshow(cloud, interpolation="bilinear")
    plt.axis("off")
    plt.title("WordCloud of Tags in Titles")
    st.pyplot(fig, True)

# --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- #
# ContentType Models Overview
# --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- #
if sl_analysis == _options[3]:
    l, r = st.columns(2)

    fig = px.pie(
        df["contentTypePred"].value_counts(sort=True),
        "contentTypePred",
        "count",
        title="Different ContentType Consumption",
    )
    l.plotly_chart(fig, True)

    fig = px.sunburst(
        df.drop_nulls("channelTitle")
        .group_by("contentTypePred", "channelTitle")
        .count()
        .filter(pl.col("count") > 30),
        path=["contentTypePred", "channelTitle"],
        values="count",
        title="Consumption of Content Type with Channel",
    )
    r.plotly_chart(fig, True)
