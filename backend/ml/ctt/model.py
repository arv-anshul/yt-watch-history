from __future__ import annotations

import re
import string
from typing import TYPE_CHECKING

import emoji
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline

if TYPE_CHECKING:
    from sklearn.base import BaseEstimator


def preprocessor(s: str) -> str:
    """Preprocessor for Vectorizer"""
    s = re.sub(r"\b\w{1,3}\b", " ", s)
    s = s.translate(str.maketrans("", "", string.punctuation + string.digits))
    s = emoji.replace_emoji(s, "")
    s = re.sub(r"\s+", " ", s)
    return s


def get_model(model: BaseEstimator) -> Pipeline:
    vectorizer = TfidfVectorizer(
        preprocessor=preprocessor,
        stop_words="english",
        ngram_range=(1, 2),
        max_features=7000,
    )
    return Pipeline([("vectorizer", vectorizer), ("model", model)])
