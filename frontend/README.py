""" README page for YouTube User History Analyser. """

import httpx
import streamlit as st

st.set_page_config("README.md", "📝", "wide")


@st.cache_resource
def fetch_intro() -> str:
    url = "https://raw.githubusercontent.com/arv-anshul/99acres-scrape/main/README.md"
    data = httpx.get(url, follow_redirects=True, timeout=3)
    return data.text


try:
    st.markdown(fetch_intro())
except httpx.HTTPError:
    st.error("Loading **README.md** failed.", icon="😢")
