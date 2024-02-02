"""
Use this script to monitor and experiment with models. These models are not for
deployment. They are just for comparision using `mlflow ui`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ml.base.monitoring import ModelMonitorBase

from .model import get_model

if TYPE_CHECKING:
    from sklearn.pipeline import Pipeline


@dataclass
class CttModelMonitor(ModelMonitorBase):
    def get_model(self) -> Pipeline:
        return get_model(self.model(**self.params))


if __name__ == "__main__":
    import mlflow
    import polars as pl
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import train_test_split
    from sklearn.naive_bayes import MultinomialNB
    from sklearn.pipeline import make_pipeline

    from ml.base.monitoring import MonitorEvaluation

    from .data import DataCleaner, DataValidator

    print("monitoring...")

    raw_data = pl.read_json("../data/ctt/channels_data.json").join(
        pl.read_json("../data/ctt/titles_data.json"), on="channelId"
    )
    # Rebuild the data transformation pipeline due to evaluation of the model.
    # If I used the pre-defined transformer from `ctt.data` module, I will not be able
    # to do evaluation on the dataset.
    data = make_pipeline(DataValidator(), DataCleaner()).fit_transform(raw_data)
    # Split the dataset into train and test set.
    # Also, not doing any preprocessing step on the cleaned data.
    X_train, X_test, y_train, y_test = train_test_split(
        data["title"], data["contentType"], test_size=0.25, random_state=42
    )

    # Monitoring different models which has completely different params with mlflow
    # is hard to compare (insight from my knowledge)
    models = {
        "rf_default": CttModelMonitor(RandomForestClassifier, {"n_estimators": 100}),
        "nb_default": CttModelMonitor(MultinomialNB, {"alpha": 1.0}),
        "nb_0.1": CttModelMonitor(MultinomialNB, {"alpha": 0.1}),
        "nb_0.2": CttModelMonitor(MultinomialNB, {"alpha": 0.2}),
        "logistic_default": CttModelMonitor(LogisticRegression),
    }

    exp_id = mlflow.create_experiment("monitor-ctt-model")
    for name, model in models.items():
        with mlflow.start_run(experiment_id=exp_id, run_name=name):
            print(name)
            monitor = MonitorEvaluation(
                model,
                {
                    "X_train": X_train,
                    "X_test": X_test,
                    "y_train": y_train,
                    "y_test": y_test,
                },
                score_type="cv",  # Calculate score using cross_validation method
            )
            model.log_model_params()
            monitor.log_model_score()
