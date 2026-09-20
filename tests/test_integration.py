"""Comprehensive end-to-end integration tests."""

import pytest
import tempfile
import numpy as np
from pathlib import Path
from lfmt.config import load_config
from lfmt.experiments import LFMTExperimentPipeline, run_parameter_sweep
from lfmt.materials import MATERIAL_DATABASE


def test_full_pipeline_end_to_end():
    config = load_config("configs/quick.yaml")
    config.simulation.spatial_resolution = {"nx": 20, "ny": 14, "nz": 8}
    config.simulation.total_time_s = 1.0
    config.simulation.timestep_s = 0.2

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        pipeline = LFMTExperimentPipeline(cache_dir=tmp_path / "cache")
        result = pipeline.run_case(config, use_cache=True)

        # Verify all bundles
        assert result.contrast_bundle.score_map.shape == (32, 32)
        assert result.matched_filter_bundle.score_map.shape == (32, 32)
        assert result.pct_bundle.score_map.shape == (32, 32)
        assert result.spct_bundle.score_map.shape == (32, 32)
        assert result.rpt_bundle.score_map.shape == (32, 32)

        # Verify dataframe contains all 5 methods
        assert len(result.metrics_dataframe) == 5
        methods = result.metrics_dataframe["method_name"].tolist()
        assert "Raw Contrast" in methods
        assert "Matched Filter" in methods
        assert "PCT" in methods
        assert "SPCT" in methods
        assert "RPT" in methods

        # Verify second execution hits cache
        result2 = pipeline.run_case(config, use_cache=True)
        assert result2.cache_hit


def test_parameter_sweep_quick():
    config = load_config("configs/quick.yaml")
    config.simulation.spatial_resolution = {"nx": 20, "ny": 14, "nz": 8}
    config.simulation.total_time_s = 1.0
    config.simulation.timestep_s = 0.2

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        df = run_parameter_sweep(
            base_config=config,
            diameters_mm=[8.0],
            depths_mm=[0.4],
            noise_levels_db=[30.0],
            output_dir=tmp_path / "sweep"
        )

        assert len(df) == 5  # 5 methods for 1 case
        assert (tmp_path / "sweep" / "sweep_results.csv").exists()
