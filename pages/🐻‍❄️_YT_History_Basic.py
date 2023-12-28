import calendar

import httpx
import numpy as np
import polars as pl
import streamlit as st
from matplotlib import pyplot as plt
from plotly import express as px
from wordcloud import STOPWORDS, WordCloud

import frontend.constants as C
from backend.api.configs import API_HOST_URL
from frontend import st_utils
from frontend.youtube import IngestYtHistory

st.set_page_config("YT Watch History", "🐻‍❄", "wide")
df = None

# Import or Upload data into app
if C.INGESTED_YT_HISTORY_DATA_PATH.exists():
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

    with st.status("Loading the data into app...", expanded=True) as status:
        df = IngestYtHistory(df_buffer).initiate()
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
        df = df.join(pred_df, on="videoId")
        df.write_json(C.INGESTED_YT_HISTORY_DATA_PATH, row_oriented=True)
        status.update(
            label="📦 Stored ingested data as JSON.", expanded=False, state="complete"
        )

    if st.button("Refresh The Page", type="primary", use_container_width=True):
        st.rerun()
    st.stop()

# Button to delete all the user's data
st_utils.delete_user_data_button()

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
        f'{df["time"].max():%b, %y} — {df["time"].min():%b, %y}',
    )
    r.metric("No. of Days of Data Present", df["time"].dt.date().n_unique())

    # No. Of Channels You Watches Frequently
    threshold = 7
    freq_ch_num = (
        df["channelTitle"].value_counts().filter(pl.col("count") > threshold).height
    )
    fig = px.pie(
        values=[freq_ch_num, df.height - freq_ch_num],
        names=["Frequently Watched Channel", "Non Freq. Channel"],
        title=f"No. of Channels You Watches Frequently [Threshold={threshold}]",
    )
    l.plotly_chart(fig, True)

    # Count Of Video Watched From Different Activity
    temp = df.select(
        "fromYtSearchHistActivity", "fromYtWatchHistActivity", "fromWebAppActivity"
    ).sum()
    fig = px.pie(
        values=temp.row(0),
        names=temp.columns,
        title="Count Of Video Watched From Different Activity",
    )
    r.plotly_chart(fig, True)

    # Top 7 Channel
    fig = px.bar(
        df["channelTitle"].value_counts(sort=True).head(7),
        "channelTitle",
        "count",
        title="Top 7 Channel You Have Watched",
    )
    st.plotly_chart(fig, True)


# --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- #
# Watch Time Insights
# --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- #
@st.cache_resource
def heatmap_with_pivot_table(
    _df: pl.DataFrame,
    index: st_utils._TimeFreqStr,
    column: st_utils._TimeFreqStr,
):
    if index == column:
        raise ValueError("index != column")

    heatmap_data = (
        _df.pivot("titleUrl", index, column, "count", sort_columns=True)
        .sort(index)
        .drop(index)
        .fill_null(0)
    )

    fig = px.imshow(
        heatmap_data,
        labels=dict(x=column.capitalize(), y=index.capitalize()),
        color_continuous_scale="YlGnBu",
        text_auto=True,
        height=700,
        aspect="auto",
    )
    fig.update_layout(
        title_x=0.33,
        title_text=f"Video Watching Patterns Over {index.capitalize()} and {column.capitalize()}",
    )

    if column == "weekday":
        fig.update_layout(
            xaxis=dict(
                tickmode="array",
                tickvals=np.arange(1, 8),
                ticktext=np.array(calendar.day_name),
            )
        )
    if index == "month":
        fig.update_layout(
            yaxis=dict(
                tickmode="array",
                tickvals=np.arange(12),
                ticktext=np.array(calendar.month_name)[1:],
            )
        )

    return fig


if sl_analysis == _options[1]:
    _freq_opt = [
        ("hour", "weekday"),
        ("hour", "year"),
        ("month", "weekday"),
        ("month", "year"),
        ("year", "weekday"),
        ("month", "hour"),
    ]
    sl_opt = st.selectbox(
        "Select Time Frequency Combination ⏰",
        _freq_opt,
        format_func=lambda x: "  —  ".join(x).title(),
    )
    fig = heatmap_with_pivot_table(df, *sl_opt)  # type: ignore
    st.plotly_chart(fig, True)


# --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- #
# WordCloud from Videos Title
# --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- #
@st.cache_resource
def generate_cloud():
    title = df.filter(
        pl.col("isShorts") == False,  # noqa: E712
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
