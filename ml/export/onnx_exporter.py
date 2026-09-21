"""
ONNX Model Exporter and Edge Runtime Latency Benchmarking for Thermographic NDT.
Supports PhysicsInformedMultiTaskNet and ThermalSpatialCNN.
"""

from __future__ import annotations
import os
import time
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import numpy as np
import torch
import torch.nn as nn

from ml.models.multitask import PhysicsInformedMultiTaskNet
from ml.models.deep_learning import ThermalSpatialCNN


def export_multitask_to_onnx(
    model: PhysicsInformedMultiTaskNet,
    output_path: str | Path,
    input_shape: Tuple[int, int, int, int] = (1, 1, 64, 64),
    physics_dim: int = 8,
    opset_version: int = 14
) -> Path:
    """
    Export PhysicsInformedMultiTaskNet to ONNX format with dynamic batch sizing.
    """
    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)

    model.eval()
    dummy_image = torch.randn(*input_shape, dtype=torch.float32)
    dummy_physics = torch.randn(input_shape[0], physics_dim, dtype=torch.float32)

    input_names = ["image_input", "physics_metadata"]
    output_names = [
        "class_logits",
        "segmentation_mask",
        "predicted_depth_mm",
        "predicted_diameter_mm",
        "predicted_centroid",
        "latent_embedding"
    ]
    dynamic_axes = {
        "image_input": {0: "batch_size"},
        "physics_metadata": {0: "batch_size"},
        "class_logits": {0: "batch_size"},
        "segmentation_mask": {0: "batch_size"},
        "predicted_depth_mm": {0: "batch_size"},
        "predicted_diameter_mm": {0: "batch_size"},
        "predicted_centroid": {0: "batch_size"},
        "latent_embedding": {0: "batch_size"},
    }

    torch.onnx.export(
        model,
        (dummy_image, dummy_physics),
        str(out_file),
        export_params=True,
        opset_version=opset_version,
        do_constant_folding=True,
        input_names=input_names,
        output_names=output_names,
        dynamic_axes=dynamic_axes
    )
    return out_file


def export_spatial_cnn_to_onnx(
    model: ThermalSpatialCNN,
    output_path: str | Path,
    input_shape: Tuple[int, int, int, int] = (1, 1, 64, 64),
    opset_version: int = 14
) -> Path:
    """
    Export ThermalSpatialCNN to ONNX format.
    """
    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)

    model.eval()
    dummy_image = torch.randn(*input_shape, dtype=torch.float32)

    input_names = ["image_input"]
    output_names = ["class_logits"]
    dynamic_axes = {
        "image_input": {0: "batch_size"},
        "class_logits": {0: "batch_size"}
    }

    torch.onnx.export(
        model,
        dummy_image,
        str(out_file),
        export_params=True,
        opset_version=opset_version,
        do_constant_folding=True,
        input_names=input_names,
        output_names=output_names,
        dynamic_axes=dynamic_axes
    )
    return out_file


def benchmark_inference_latency(
    model: nn.Module,
    input_shape: Tuple[int, int, int, int] = (1, 1, 64, 64),
    n_warmup: int = 10,
    n_eval: int = 50
) -> Dict[str, float]:
    """
    Benchmark PyTorch CPU inference latency (mean, median, p95 in milliseconds).
    """
    model.eval()
    dummy_input = torch.randn(*input_shape)
    is_multitask = isinstance(model, PhysicsInformedMultiTaskNet)
    dummy_physics = torch.randn(input_shape[0], getattr(model, "physics_dim", 8)) if is_multitask else None

    # Warmup
    with torch.no_grad():
        for _ in range(n_warmup):
            if is_multitask:
                _ = model(dummy_input, dummy_physics)
            else:
                _ = model(dummy_input)

    # Benchmark
    latencies = []
    with torch.no_grad():
        for _ in range(n_eval):
            t0 = time.perf_counter()
            if is_multitask:
                _ = model(dummy_input, dummy_physics)
            else:
                _ = model(dummy_input)
            t1 = time.perf_counter()
            latencies.append((t1 - t0) * 1000.0)

    latencies_arr = np.array(latencies)
    return {
        "mean_latency_ms": float(np.mean(latencies_arr)),
        "median_latency_ms": float(np.median(latencies_arr)),
        "p95_latency_ms": float(np.percentile(latencies_arr, 95)),
        "min_latency_ms": float(np.min(latencies_arr)),
        "max_latency_ms": float(np.max(latencies_arr)),
        "fps": float(1000.0 / np.mean(latencies_arr)) if np.mean(latencies_arr) > 0 else 0.0
    }
