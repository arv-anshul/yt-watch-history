""" README page for YouTube User History Analyser. """

from pathlib import Path

import streamlit as st

st.set_page_config("README.md", "📝", "wide")

README_PATH = Path("README.md")

try:
    st.markdown(README_PATH.read_text())
except FileNotFoundError:
    st.error("README.md file not found.", icon="😢")
