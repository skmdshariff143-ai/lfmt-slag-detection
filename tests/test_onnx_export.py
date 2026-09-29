"""
Unit tests for ONNX export and edge runtime latency benchmarking.
"""

import os
import tempfile
from pathlib import Path
import pytest
import torch

from ml.models.multitask import PhysicsInformedMultiTaskNet
from ml.models.deep_learning import ThermalSpatialCNN
from ml.export.onnx_exporter import (
    export_multitask_to_onnx,
    export_spatial_cnn_to_onnx,
    benchmark_inference_latency,
)


def test_export_multitask_to_onnx():
    """Verify export of PhysicsInformedMultiTaskNet to ONNX file format."""
    model = PhysicsInformedMultiTaskNet(in_channels=1, num_classes=5, physics_dim=8)
    with tempfile.TemporaryDirectory() as tmpdir:
        onnx_file = Path(tmpdir) / "multitask_model.onnx"
        exported_path = export_multitask_to_onnx(
            model=model,
            output_path=onnx_file,
            input_shape=(1, 1, 32, 32),
            physics_dim=8
        )
        assert exported_path.exists()
        assert exported_path.stat().st_size > 1000  # Non-empty binary


def test_export_spatial_cnn_to_onnx():
    """Verify export of ThermalSpatialCNN to ONNX file format."""
    model = ThermalSpatialCNN(in_channels=1, num_classes=2)
    with tempfile.TemporaryDirectory() as tmpdir:
        onnx_file = Path(tmpdir) / "spatial_cnn.onnx"
        exported_path = export_spatial_cnn_to_onnx(
            model=model,
            output_path=onnx_file,
            input_shape=(1, 1, 32, 32)
        )
        assert exported_path.exists()
        assert exported_path.stat().st_size > 1000


def test_benchmark_inference_latency():
    """Verify latency benchmarking utility executes and returns valid metrics."""
    model = ThermalSpatialCNN(in_channels=1, num_classes=2)
    metrics = benchmark_inference_latency(model, input_shape=(1, 1, 32, 32), n_warmup=2, n_eval=5)
    assert "mean_latency_ms" in metrics
    assert "fps" in metrics
    assert metrics["mean_latency_ms"] > 0
    assert metrics["fps"] > 0
