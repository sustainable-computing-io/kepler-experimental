import json
import logging
import os
import pathlib
import typing
from datetime import datetime
from typing import NamedTuple

# TODO: delete me
import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import PolynomialFeatures, StandardScaler
from tabulate import tabulate
from xgboost import XGBRegressor

from power_model.datasource import prometheus

logger = logging.getLogger(__name__)


def save_to_json(data, path):
    with open(path, "w") as json_file:
        json.dump(data, json_file)


class ErrorMetrics(NamedTuple):
    mae: float
    mse: float
    mape: float
    r2: float


def calculate_metrics(y_true, y_pred) -> ErrorMetrics:
    mae = mean_absolute_error(y_true, y_pred)
    mse = mean_squared_error(y_true, y_pred)
    r2 = 0.0
    if len(y_true) > 5:
        r2 = r2_score(y_true, y_pred)

    assert type(r2) is float

    mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100  # MAPE calculation
    return ErrorMetrics(mae, mse, mape, r2)


def train_one(name: str, pipeline: Pipeline, X, y, model_path: pathlib.Path) -> tuple[Pipeline, ErrorMetrics]:
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

    pipeline.fit(X_train, y_train)
    # find accuracy
    y_pred = pipeline.predict(X_test)
    metrics = calculate_metrics(y_test, y_pred)

    # Save model with Joblib
    joblib.dump(pipeline, os.path.join(model_path, f"{name}_model.joblib"))
    save_to_json(metrics._asdict(), os.path.join(model_path, f"{name}_model_error.json"))

    return pipeline, metrics


# TODO: fix typing.Any
def pipeline_for_model_name(name: str, params: dict[str, typing.Any]) -> Pipeline:
    if name == "xgboost":
        return Pipeline(
            [
                ("scaler", StandardScaler()),
                ("xgboost", XGBRegressor(**params)),
            ]
        )
    if name == "linear":
        return Pipeline(
                [
                    ("scaler", StandardScaler()),
                    ("linear", LinearRegression(**params)),

                ]
        )
    if name == "polynomial":
        return Pipeline(
            [
                ("scaler", StandardScaler()),
                ("poly_features", PolynomialFeatures(**params)),
                ("linear", LinearRegression()),  # or any other model you wish to use
            ]
        )
        # poly = PolynomialFeatures(**params)
        # return make_pipeline(poly, LinearRegression())

    # if name == "logistic":
    #     return LogisticRegression(**params)

    raise ValueError(f"Invalid model name: {name}")


def train_models(X, y, models: dict[str, typing.Any], base_dir: pathlib.Path):
    trained_models = {}
    metrics = {}

    model_path = pathlib.Path(base_dir) / "models"
    os.makedirs(model_path, exist_ok=True)

    for name, params in models.items():
        regressor = pipeline_for_model_name(name, params or {})
        model, err_metrics = train_one(name, regressor, X, y, model_path)
        trained_models[name] = model
        metrics[name] = err_metrics

    return trained_models, metrics


def create_model_for_feature(
    name: str,
    features: list[str],
    df: pd.DataFrame,
    train_path: pathlib.Path,
    models: dict[str, typing.Any],
):
    # Prepare training data (X and y)
    # ipdb.set_trace()

    # input_data = pd.DataFrame(numpy_array, columns=['feature1', 'feature2', ...])
    X = df[features] # .rolling(3).mean().dropna()
    y = df["target"] # .rolling(3).mean().dropna()

    model_base_path = train_path / name
    os.makedirs(model_base_path, exist_ok=True)
    df.to_csv(model_base_path / "training_inputs.csv")

    trained_models, metrics = train_models(X, y, models, model_base_path)
    # Save results to JSON file
    save_to_json({m: metrics[m]._asdict() for m in metrics.keys()}, model_base_path / "model_errors.json")

    table_data = []
    for model, metrics in metrics.items():
        table_data.append([model, metrics.mape, metrics.mae, metrics.mse, metrics.r2])

    # Print the table
    print(f"              {name}")
    print("----------------------------------")
    print(tabulate(table_data, headers=["Name", "MAPE", "MAE", "MSE", "R2"], tablefmt="tabulate"))


def train(config):
    prometheus_url = config["prometheus"]["url"]
    prom = prometheus.Client(prometheus_url)

    start_at: datetime = config["train"]["start_at"]
    end_at: datetime = config["train"]["end_at"]
    step = config["train"]["step"]

    target_query = config["train"]["target"]

    df_target = prom.range_query(start=start_at, end=end_at, step=step, target=target_query)

    pipelines = config["train"]["pipelines"]
    train_path = pathlib.Path(config["train"]["path"])

    for pipeline in pipelines:
        name = pipeline["name"]
        features = pipeline["features"]
        df_features = prom.range_query(start=start_at, end=end_at, step=step, **features)
        df = pd.merge(df_features, df_target, on="timestamp")
        df.info()
        create_model_for_feature(name, features.keys(), df, train_path, config["train"]["models"])


class Predictor:
    def __init__(self, pipeline):
        self.pipeline = pipeline

        self.prom = prometheus.Client(pipeline["prometheus"]["url"])
        train = pipeline["train"]
        model_path = pathlib.Path(train["path"])

        self.pipelines = train["pipelines"]
        pipeline_names = [p["name"] for p in self.pipelines]

        models = train["models"]
        self.models = {
            name: {m: joblib.load(model_path / name / "models" / f"{m}_model.joblib") for m in models}
            for name in pipeline_names
        }

        self.target = train["target"]
        self.step = train["step"]

    def predict_range(self, start, end, step=None):
        step = step or self.step

        summary = []
        for pipeline in self.pipelines:
            pipeline_name = pipeline["name"]
            features = pipeline["features"]

            df_features = self.prom.range_query(start=start, end=end, step=step, **features)
            df_y = self.prom.range_query(start=start, end=end, step=step, target=self.target)

            X = df_features[features.keys()]
            y = df_y["target"]

            for model_name, model in self.models[pipeline_name].items():
                y_pred = model.predict(X)
                metrics = calculate_metrics(y, y_pred)
                summary.append([pipeline_name, model_name, metrics.mape, metrics.mae, metrics.mse, metrics.r2])
            summary.append([])

        print(
            tabulate(
                summary,
                headers=["Name", "MAPE", "MAE", "MSE", "R2"],
                tablefmt="tabulate",
            )
        )

    def predict(self, at=None):
        if at is None:
            at = datetime.now()

        df_y = self.prom.instant_query(at=at, target=self.target)
        y_val = df_y["target"].values

        for pipeline in self.pipelines:
            pipeline_name = pipeline["name"]
            features = pipeline["features"]
            df_features = self.prom.instant_query(at=at, **features)
            X = df_features[features.keys()]

            table = []

            for model_name, model in self.models[pipeline_name].items():
                y_pred = model.predict(X)
                diff = y_val - y_pred
                percent_error = np.round(abs(diff / y_val) * 100, 2)

                row = [pipeline_name, model_name]

                # ipdb.set_trace()
                row = np.append(row, *X.values)
                row = np.append(row, *y_val)
                row = np.append(row, *y_pred)

                percent_error = np.round(abs(diff / y_val) * 100, 2)
                row = np.append(row, [np.round(diff, 2), percent_error])
                table.append(row.tolist())

            print(
                tabulate(
                    table,
                    headers=["Pipeline", "Name", *features.keys(), "Target", "Predicted", "Diff", "Err %"],
                    tablefmt="tabulate",
                )
            )

