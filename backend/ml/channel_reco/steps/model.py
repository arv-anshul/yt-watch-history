import re
import string

import emoji
from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import TfidfVectorizer


def preprocess_title(s: str) -> str:
    """Preprocessor for vectorizer to preprocess titles data."""
    s = re.sub(r"\b\w{1,3}\b", " ", s)
    s = s.translate(str.maketrans("", "", string.punctuation + string.digits))
    s = emoji.replace_emoji(s, "")
    s = re.sub(r"\s+", " ", s)
    s = s.lower()
    return s


def preprocess_tags(s: str) -> str:
    """Preprocessor for vectorizer to preprocess titles data."""
    s = re.sub(r"\b\w{1,2}\b", " ", s)
    s = s.translate(str.maketrans("", "", string.punctuation + string.digits))
    s = emoji.replace_emoji(s, "")
    s = re.sub(r"\s+", " ", s)
    s = s.lower()
    return s


def get_vectorizer() -> ColumnTransformer:
    title_transformer = TfidfVectorizer(
        max_features=7000,
        ngram_range=(1, 2),
        preprocessor=preprocess_title,
        stop_words="english",
    )
    tags_transformer = TfidfVectorizer(
        max_features=5000,
        ngram_range=(1, 2),
        preprocessor=preprocess_tags,
        stop_words="english",
    )
    transformer = ColumnTransformer(
        [
            ("title_trf", title_transformer, "title"),
            ("tags_trf", tags_transformer, "tags"),
        ]
    )
    return transformer
