from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Literal

import mlflow
from sklearn.model_selection import StratifiedKFold, cross_val_score

if TYPE_CHECKING:
    from sklearn.base import BaseEstimator

    from ml.typing import DataDict


@dataclass(eq=False)
class ModelMonitorBase(ABC):
    model: type[BaseEstimator]
    params: dict[str, Any] = field(default_factory=dict)

    @abstractmethod
    def get_model(self) -> Any:
        ...

    def log_model_params(self) -> None:
        if self.params:
            mlflow.log_params(self.params)


@dataclass(eq=False, frozen=True)
class MonitorEvaluation:
    model: ModelMonitorBase
    data_dict: DataDict
    score_type: Literal["default", "cv"] = field(default="default", kw_only=True)

    def _fit_model(self, model: ModelMonitorBase) -> Any:
        _model = model.get_model()
        _model.fit(
            self.data_dict["X_train"],
            self.data_dict["y_train"],
        )
        return _model

    def cv_score(self, model: ModelMonitorBase) -> float:
        """
        Calculate model score using `cross_val_score` from `sklearn` library function.
        """
        cv_fold = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
        cv_score = cross_val_score(
            model.get_model(),
            self.data_dict["X_train"].to_pandas(),
            self.data_dict["y_train"],
            cv=cv_fold,
        )
        return cv_score.mean()

    def score(self, model: ModelMonitorBase) -> float:
        """Calculate model score with builtin `.score()` method."""
        _model = self._fit_model(model)
        return float(
            _model.score(
                self.data_dict["X_test"],
                self.data_dict["y_test"],
            )
        )

    def calc_score(self) -> float:
        """Calculate scores of all models with the specified `score_type`."""
        scoring_func = self.cv_score if self.score_type == "cv" else self.score
        return scoring_func(self.model)

    def log_model_score(self) -> None:
        """Log model score using mlflow."""
        mlflow.log_metric("score", self.calc_score())
