"""Optional, local-only MLflow tracking for a complete conference study."""
from __future__ import annotations

import csv
import hashlib
import importlib
from contextlib import contextmanager
from pathlib import Path
from typing import Callable, Iterator, Protocol, cast


class TrackingAPI(Protocol):
    def set_tracking_uri(self, uri: str) -> None: ...
    def set_experiment(self, name: str) -> object: ...
    def start_run(self, *, run_name: str) -> object: ...
    def log_params(self, params: dict[str, str]) -> None: ...
    def log_metric(self, key: str, value: float) -> None: ...
    def log_artifact(self, local_path: str) -> None: ...
    def end_run(self, status: str = "FINISHED") -> None: ...


class TrackingClient(Protocol):
    def get_experiment_by_name(self, name: str) -> object | None: ...
    def create_experiment(self, name: str, *, artifact_location: str) -> str: ...


@contextmanager
def track_study(directory: Path | None, output: Path, config: Path) -> Iterator[None]:
    """Track success and failures, with a local SQLite store and local artifacts.

    Import is lazy, so classical users need no tracking dependency. Only aggregate
    metrics and small provenance artifacts are recorded, never raw thermal cubes.
    """
    if directory is None:
        yield
        return
    mlflow = cast(TrackingAPI, importlib.import_module("mlflow"))
    directory = directory.resolve()
    directory.mkdir(parents=True, exist_ok=True)
    mlflow.set_tracking_uri("sqlite:///" + (directory / "tracking.db").as_posix())
    # A unique experiment path gives MLflow an explicit local artifact location.
    client_factory = cast(Callable[[], TrackingClient], importlib.import_module("mlflow.tracking").MlflowClient)
    client = client_factory()
    name = "lfmt-conference-" + hashlib.sha256(str(directory).encode()).hexdigest()[:12]
    if client.get_experiment_by_name(name) is None:
        client.create_experiment(name, artifact_location=(directory / "artifacts").as_uri())
    mlflow.set_experiment(name)
    mlflow.start_run(run_name=output.name)
    try:
        mlflow.log_params({"config_sha256": hashlib.sha256(config.read_bytes()).hexdigest(),
                           "output_directory": str(output.resolve())})
        mlflow.log_artifact(str(config))
        yield
        raw = output / "raw_results.csv"
        if raw.exists():
            with raw.open(encoding="utf-8", newline="") as stream:
                records = list(csv.DictReader(stream))
            for method in sorted({row["method"] for row in records}):
                defects = [row for row in records if row["method"] == method and row["is_healthy"].lower() != "true"]
                healthy = [row for row in records if row["method"] == method and row["is_healthy"].lower() == "true"]
                key = method.replace(" ", "_")
                if defects:
                    mlflow.log_metric(key + "/detection_rate", sum(row["is_detected"].lower() == "true" for row in defects) / len(defects))
                    mlflow.log_metric(key + "/mean_iou", sum(float(row["iou"]) for row in defects) / len(defects))
                if healthy:
                    mlflow.log_metric(key + "/false_alarm_rate", sum(row["is_false_positive"].lower() == "true" for row in healthy) / len(healthy))
        for name in ["experiment_manifest.json", "summary_by_method.csv", "healthy_specificity.csv"]:
            if (output / name).exists():
                mlflow.log_artifact(str(output / name))
    except BaseException:
        mlflow.end_run(status="FAILED")
        raise
    else:
        mlflow.end_run(status="FINISHED")
