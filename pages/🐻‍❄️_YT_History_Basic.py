import calendar

import numpy as np
import polars as pl
import streamlit as st
from matplotlib import pyplot as plt
from plotly import express as px
from sklearn.feature_extraction.text import TfidfVectorizer
from wordcloud import STOPWORDS, WordCloud

import frontend.constants as C
from frontend import _io, st_utils
from frontend.youtube import ContentTypeTagging, IngestYtHistory

st.set_page_config("YT Watch History", "🐻‍❄", "wide")
df = None

# Import or Upload data into app
if C.INGESTED_YT_HISTORY_DATA_PATH.exists():
    df = st_utils.get_ingested_yt_history_df()
else:
    with st.form("upload-yt-history-data"):
        df_buffer = st.file_uploader("Upload dataset (.json)", type=".json")
        use_shorts = st.checkbox(
            "Use **YT Shorts** data for training.", help="Not Recommended!"
        )
        force_build = st.checkbox(
            "Force to re-build the **ContentType** prediction model.",
            help="Not Recommended!",
        )
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
        if not ContentTypeTagging.check_content_type_model_exists():
            status.write(":orange[⚙️ Building ContentType prediction model.]")
            ContentTypeTagging(use_shorts=use_shorts).build(force=force_build)
            status.write(":green[🥳 ContentType prediction model has been created.]")

        # Predict the videos ContentType
        if "contentType" not in df.columns:
            status.write(":orange[🤔 Predicting the videos ContentType.]")
            df = ContentTypeTagging.predict(df)
            status.write(":green[🎊 Prediction compleated!]")
            df.write_json(C.INGESTED_YT_HISTORY_DATA_PATH, row_oriented=True)
            status.update(
                label="📦 Stored the ContentType details data.",
                expanded=False,
                state="complete",
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
        df["channelTitle"].value_counts().filter(pl.col("counts") > threshold).height
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
        "counts",
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
    vectorizer: TfidfVectorizer = _io.load_object(C.CONTENT_TYPE_VEC_PATH)
    preprocessor = vectorizer.build_preprocessor()
    title = df.filter(
        pl.col("isShorts") == False,  # noqa: E712
    ).select(
        pl.col("title").str.replace(r"#\w+", ""),
    )
    text = " ".join([preprocessor(s) for s in title["title"]])
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
    # Import all the models
    vectorizer, label_enc, model = ContentTypeTagging.load_objects()

    with st.expander("📁 Details About Model", True):
        ctt = ContentTypeTagging()
        acc_score = st.cache_resource(ctt.model_acc_score)()

        l, m, r = st.columns(3)
        l.metric("Model Name", type(model).__name__)
        m.metric("Model Accuracy", f"{acc_score*100:.2f}")

    with st.expander("🛠️ :orange[Vectorize Your Texts]"):
        text_from_user = st.text_input("Enter a random title", max_chars=111)
        if text_from_user:
            text_vec = vectorizer.transform([text_from_user])
            content_type = label_enc.inverse_transform(model.predict(text_vec))
            st.write(
                "#### :red[Text after Vectorizaiton:] "
                f"**`{list(vectorizer.inverse_transform(text_vec)[0])}`**"
            )
            st.write(f"#### :red[Content Type:] **`{content_type[0]}`**")

    l, r = st.columns(2)

    fig = px.pie(
        df["contentType"].value_counts(sort=True),
        "contentType",
        "counts",
        title="Different ContentType Consumption",
    )
    l.plotly_chart(fig, True)

    fig = px.sunburst(
        df.drop_nulls("channelTitle")
        .group_by("contentType", "channelTitle")
        .count()
        .filter(pl.col("count") > 30),
        path=["contentType", "channelTitle"],
        values="count",
        title="Consumption of Content Type with Channel",
    )
    r.plotly_chart(fig, True)
