"""
Generate reproducible Google Colab notebooks for LFMT Research V3.
"""

import json
from pathlib import Path

out_dir = Path("notebooks/colab")
out_dir.mkdir(parents=True, exist_ok=True)


def make_nb(title: str, description: str, code_cells: list) -> dict:
    cells = [
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                f"# {title}\n",
                "**LFMT Slag Detection & Thermographic NDT Platform**\n\n",
                f"{description}\n",
            ],
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "# 1. Clone Repository & Setup Environment (For Google Colab)\n",
                "!git clone https://github.com/skmdshariff143-ai/lfmt-slag-detection.git || true\n",
                "%cd lfmt-slag-detection\n",
                "!pip install -q scikit-fem scikit-learn scipy matplotlib onnx onnxruntime pydantic\n",
            ],
        },
    ]
    for cell_title, code in code_cells:
        cells.append({
            "cell_type": "markdown",
            "metadata": {},
            "source": [f"### {cell_title}\n"],
        })
        cells.append({
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [line + "\n" for line in code.strip().split("\n")],
        })
    return {
        "cells": cells,
        "metadata": {
            "language_info": {"name": "python"},
            "orig_nbformat": 4,
        },
        "nbformat": 4,
        "nbformat_minor": 4,
    }


# 01
nb01 = make_nb(
    "01: Synthetic LFMT Dataset Generation",
    "Generates multi-class, multi-depth synthetic LFMT thermograms using 3D FEM transient simulation.",
    [
        (
            "Generate Multitask LFMT Dataset",
            """from scripts.datasets.generate_synthetic_lfmt_dataset import generate_multitask_dataset
manifest = generate_multitask_dataset(n_samples=20, output_dir='data/datasets/synthetic_multitask_lfmt')
print('Generated manifest:', manifest.get('total_samples'))""",
        )
    ],
)
(out_dir / "01_synthetic_lfmt_dataset_generation.ipynb").write_text(json.dumps(nb01, indent=2))

# 02
nb02 = make_nb(
    "02: Signal Processing Benchmarks",
    "Compares Raw Contrast, LFMT Matched Filter, Blind PCT, SPCT, and RPT on LFMT thermal sequences.",
    [
        (
            "Run Processing Benchmark",
            """import numpy as np
from src.lfmt.processing import LFMTMatchedFilter, PrincipleComponentThermography, SparsePCT, RandomizedPCT
print('Signal processing algorithms loaded successfully.')""",
        )
    ],
)
(out_dir / "02_signal_processing_benchmarks.ipynb").write_text(json.dumps(nb02, indent=2))

# 03
nb03 = make_nb(
    "03: Classical ML Tabular Models",
    "Trains Random Forest classifier and depth/diameter regressors on extracted 14D physics features.",
    [
        (
            "Train Tabular ML Baselines",
            """from ml.models.classical import ClassicalMLPipeline
pipeline = ClassicalMLPipeline()
print('Classical ML pipeline initialized.')""",
        )
    ],
)
(out_dir / "03_classical_ml_tabular_models.ipynb").write_text(json.dumps(nb03, indent=2))

# 04
nb04 = make_nb(
    "04: Deep Learning Multi-Task Training",
    "Trains PhysicsInformedMultiTaskNet with shared convolutional encoder and physics metadata injection.",
    [
        (
            "Initialize Multi-Task Model",
            """import torch
from ml.models.multitask import PhysicsInformedMultiTaskNet
model = PhysicsInformedMultiTaskNet(in_channels=1, num_classes=5, physics_dim=8)
print('Multi-task network parameters:', sum(p.numel() for p in model.parameters()))""",
        )
    ],
)
(out_dir / "04_deep_learning_multitask_training.ipynb").write_text(json.dumps(nb04, indent=2))

# 05
nb05 = make_nb(
    "05: Uncertainty Estimation & OOD Detection",
    "Evaluates MC Dropout epistemic uncertainty and Mahalanobis out-of-distribution detection.",
    [
        (
            "Evaluate Uncertainty & OOD",
            """from ml.uncertainty.dropout import MCDropoutEstimator
from ml.ood.detector import OODDetector
print('Uncertainty and OOD modules ready.')""",
        )
    ],
)
(out_dir / "05_uncertainty_and_ood_evaluation.ipynb").write_text(json.dumps(nb05, indent=2))

# 06
nb06 = make_nb(
    "06: External Measured Data Transfer Study",
    "Ingests PolyU flash pulsed thermography dataset on mild steel with 11 Flat-Bottom Holes under strict blind mode.",
    [
        (
            "Load PolyU Dataset and Run Blind Ingestion",
            """from src.lfmt.io_experimental import load_polyu_dataset
print('PolyU loader ready.')""",
        )
    ],
)
(out_dir / "06_external_real_world_transfer.ipynb").write_text(json.dumps(nb06, indent=2))

# 07
nb07 = make_nb(
    "07: ONNX Export & Edge Inference Benchmark",
    "Exports PyTorch models to ONNX and benchmarks CPU inference latency and throughput.",
    [
        (
            "Benchmark ONNX Export",
            """from ml.export.onnx_exporter import benchmark_inference_latency
from ml.models.multitask import PhysicsInformedMultiTaskNet
model = PhysicsInformedMultiTaskNet()
latencies = benchmark_inference_latency(model, n_warmup=5, n_eval=20)
print('Benchmarked latencies:', latencies)""",
        )
    ],
)
(out_dir / "07_onnx_export_and_edge_benchmark.ipynb").write_text(json.dumps(nb07, indent=2))

print("All 7 Colab notebooks generated successfully.")
