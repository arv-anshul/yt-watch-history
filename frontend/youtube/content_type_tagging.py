import string
import warnings

import polars as pl
from nltk.stem import PorterStemmer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.preprocessing import LabelEncoder

import frontend.constants as C
from frontend import _io

warnings.filterwarnings("ignore", category=UserWarning)


class ContentTypeTagging:
    def __init__(self, *, use_shorts: bool = False) -> None:
        df = self.merge_dataset(use_shorts=use_shorts)
        X, y = df["title"], df["contentType"]
        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
            X, y, test_size=0.25, random_state=42
        )

    @classmethod
    def get_content_type_tagged_channel_df(cls) -> pl.DataFrame:
        df = pl.read_json(C.CONTENT_TYPE_TAGGED_CHANNEL_DATASET_PATH)
        tagged_ch_df = pl.DataFrame(
            {
                "channelName": df.columns,
                "contentType": df.transpose().to_series(),
            }
        )
        return tagged_ch_df

    def merge_dataset(
        self,
        *,
        use_shorts: bool = False,
    ) -> pl.DataFrame:
        tagged_ch_df = ContentTypeTagging.get_content_type_tagged_channel_df()
        history_df = pl.read_json(C.INGESTED_YT_HISTORY_DATA_PATH)
        if use_shorts is False:
            history_df = history_df.filter(pl.col("isShorts") == use_shorts)

        # Merge both dataset by the channel names
        df = tagged_ch_df.join(history_df, on="channelName").select(
            "title", "contentType"
        )
        return df

    def __preprocessor(self, s: str):
        """Preprocessor for Vectorizer."""
        s = s.translate(str.maketrans("", "", string.punctuation))
        ps = PorterStemmer()
        s = " ".join([ps.stem(i) for i in s.split() if i.isascii()])
        return s

    @classmethod
    def check_content_type_model_exists(cls, ignore: bool = False) -> bool:
        return _io.paths_exists(
            C.CONTENT_TYPE_VEC_PATH,
            C.CONTENT_TYPE_LABEL_ENC_PATH,
            C.CONTENT_TYPE_MODEL_PATH,
            ignore=ignore,
        )

    def build(
        self,
        *,
        force: bool = False,
    ) -> None:
        if ContentTypeTagging.check_content_type_model_exists(ignore=force):
            raise FileExistsError(
                "Model is already build. Delete previous to re-build."
            )

        # Get Vectorizer
        vectorizer = TfidfVectorizer(
            preprocessor=self.__preprocessor,
            max_features=7_000,
            ngram_range=(1, 2),
            stop_words="english",
        )
        X_vec = vectorizer.fit_transform(self.X_train)

        # Encode Labels
        label_enc = LabelEncoder()
        y_enc = label_enc.fit_transform(self.y_train)  # Encode y_train's labels

        # Finally, train model
        model = MultinomialNB()
        model.fit(X_vec, y_enc)

        # Store models and objects
        _io.store_object(vectorizer, C.CONTENT_TYPE_VEC_PATH)
        _io.store_object(label_enc, C.CONTENT_TYPE_LABEL_ENC_PATH)
        _io.store_object(model, C.CONTENT_TYPE_MODEL_PATH)

    @staticmethod
    def load_objects() -> tuple[TfidfVectorizer, LabelEncoder, MultinomialNB]:
        if not ContentTypeTagging.check_content_type_model_exists():
            raise FileNotFoundError("Build the model first.")
        vectorizer, label_enc, model = _io.load_objects(
            C.CONTENT_TYPE_VEC_PATH,
            C.CONTENT_TYPE_LABEL_ENC_PATH,
            C.CONTENT_TYPE_MODEL_PATH,
        )
        return vectorizer, label_enc, model

    def model_acc_score(self) -> float:
        if not ContentTypeTagging.check_content_type_model_exists():
            raise FileNotFoundError("Build the model first.")
        vectorizer, label_enc, model = ContentTypeTagging.load_objects()

        X_vec = vectorizer.transform(self.X_test)
        y_vec = label_enc.transform(self.y_test)

        y_pred = model.predict(X_vec)
        score = accuracy_score(y_vec, y_pred)
        return float(score)

    @staticmethod
    def predict(df: pl.DataFrame) -> pl.DataFrame:
        if not ContentTypeTagging.check_content_type_model_exists():
            raise FileNotFoundError("Build the model first.")
        vectorizer, label_enc, model = ContentTypeTagging.load_objects()

        X = vectorizer.transform(df["title"])
        y_pred = model.predict(X)
        df = df.with_columns(
            pl.lit(label_enc.inverse_transform(y_pred)).alias("contentType")
        )
        return df
