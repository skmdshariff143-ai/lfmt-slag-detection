"""Unit tests for configuration loading and validation."""

import pytest
from pathlib import Path
from lfmt.config import load_config, LFMTConfig


def test_load_default_config():
    config_path = Path("configs/default.yaml")
    config = load_config(config_path)
    assert isinstance(config, LFMTConfig)
    assert config.geometry.plate.length_mm == 100.0
    assert config.geometry.plate.material == "mild_steel"
    assert config.geometry.inclusion.diameter_mm == 8.0
    assert config.geometry.inclusion.depth_mm == 0.6


def test_load_quick_config():
    config_path = Path("configs/quick.yaml")
    config = load_config(config_path)
    assert config.simulation.spatial_resolution["nx"] == 40
    assert config.camera.resolution_x == 32


def test_config_geometry_validation():
    config = load_config("configs/default.yaml")
    # Set defect depth + thickness greater than plate thickness
    config.geometry.inclusion.depth_mm = 2.0
    config.geometry.inclusion.thickness_mm = 1.0  # 2.0 + 1.0 = 3.0 > 2.3 mm plate
    with pytest.raises(ValueError, match="exceeds plate thickness"):
        config.validate()
