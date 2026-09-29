"""Real local MLflow lifecycle checks, no tracking service or simulated client."""
from pathlib import Path

import pytest

from lfmt.experiment_tracking import track_study


def test_local_tracking_success_and_failure(tmp_path: Path):
    mlflow = pytest.importorskip("mlflow")
    from mlflow.tracking import MlflowClient
    config = tmp_path / "config.yaml"
    config.write_text("seed: 42\n", encoding="utf-8")
    output = tmp_path / "study"
    output.mkdir()
    (output / "raw_results.csv").write_text(
        "method,is_healthy,is_detected,is_false_positive,iou\n"
        "MF,False,True,False,0.5\nMF,True,False,True,0\n", encoding="utf-8")
    with track_study(tmp_path / "tracking", output, config):
        pass
    with pytest.raises(RuntimeError, match="deliberate failure"):
        with track_study(tmp_path / "tracking", output, config):
            raise RuntimeError("deliberate failure")
    client = MlflowClient()
    runs = client.search_runs([e.experiment_id for e in client.search_experiments()])
    assert sorted(run.info.status for run in runs) == ["FAILED", "FINISHED"]
    completed = next(run for run in runs if run.info.status == "FINISHED")
    assert completed.data.metrics["MF/detection_rate"] == 1
    assert completed.data.metrics["MF/false_alarm_rate"] == 1
    assert completed.data.metrics["MF/mean_iou"] == .5
    assert any(a.path == "config.yaml" for a in client.list_artifacts(completed.info.run_id))
    assert mlflow.active_run() is None
