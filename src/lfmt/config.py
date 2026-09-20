"""
Configuration management system for LFMT slag detection framework.
"""

from __future__ import annotations
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, List, Optional
import yaml


@dataclass
class PlateConfig:
    length_mm: float = 100.0
    width_mm: float = 70.0
    thickness_mm: float = 2.3
    material: str = "mild_steel"
    thermal_conductivity: Optional[float] = None
    density: Optional[float] = None
    specific_heat: Optional[float] = None

    def __post_init__(self):
        if self.length_mm <= 0 or self.width_mm <= 0 or self.thickness_mm <= 0:
            raise ValueError("Plate dimensions must be strictly positive.")


@dataclass
class InclusionConfig:
    shape: str = "cylinder"
    center_x_mm: float = 50.0
    center_y_mm: float = 35.0
    depth_mm: float = 0.6
    diameter_mm: float = 8.0
    thickness_mm: float = 0.5
    material: str = "slag"
    thermal_conductivity: Optional[float] = None
    density: Optional[float] = None
    specific_heat: Optional[float] = None

    def __post_init__(self):
        if self.depth_mm < 0:
            raise ValueError(f"Inclusion depth must be >= 0, got {self.depth_mm}")
        if self.diameter_mm < 0 or self.thickness_mm <= 0:
            raise ValueError("Inclusion thickness must be strictly positive and diameter >= 0.")


@dataclass
class GeometryConfig:
    plate: PlateConfig = field(default_factory=PlateConfig)
    inclusion: InclusionConfig = field(default_factory=InclusionConfig)


@dataclass
class ExcitationConfig:
    type: str = "linear_chirp"
    f0_hz: float = 0.05
    f1_hz: float = 0.50
    duration_s: float = 10.0
    q0_w_m2: float = 5000.0
    ambient_temp_k: float = 293.15
    h_conv_w_m2k: float = 10.0
    emissivity: float = 0.95


@dataclass
class SimulationConfig:
    backend: str = "finite_difference"  # "fem" or "finite_difference"
    spatial_resolution: Dict[str, int] = field(
        default_factory=lambda: {"nx": 80, "ny": 56, "nz": 24}
    )
    timestep_s: float = 0.05
    total_time_s: float = 12.0


@dataclass
class CameraConfig:
    resolution_x: int = 64
    resolution_y: int = 64
    sampling_rate_hz: float = 10.0
    lens_fov_mm: List[float] = field(default_factory=lambda: [100.0, 70.0])


@dataclass
class NoiseConfig:
    snr_db: Optional[float] = None  # None (clean), 30, 25, 20
    spatial_nonuniformity: float = 0.005
    emissivity_variation: float = 0.005
    seed: int = 42


@dataclass
class PCTConfig:
    n_components: int = 6
    selection_criterion: str = "contrast"  # "contrast", "snr", "blind_kurtosis"


@dataclass
class SPCTConfig:
    n_components: int = 6
    alpha: float = 0.05
    max_iter: int = 200


@dataclass
class RPTConfig:
    n_components: int = 6
    matrix_type: str = "gaussian"


@dataclass
class DetectionConfig:
    threshold_method: str = "adaptive_otsu"
    morphology_kernel_size: int = 3
    min_area_px: int = 4


@dataclass
class ProcessingConfig:
    pct: PCTConfig = field(default_factory=PCTConfig)
    spct: SPCTConfig = field(default_factory=SPCTConfig)
    rpt: RPTConfig = field(default_factory=RPTConfig)
    matched_filter: Dict[str, Any] = field(
        default_factory=lambda: {"normalize": True, "zero_pad": True}
    )
    detection: DetectionConfig = field(default_factory=DetectionConfig)


@dataclass
class LFMTConfig:
    project: Dict[str, Any] = field(
        default_factory=lambda: {"name": "LFMT Slag Detection", "version": "0.1.0", "random_seed": 42}
    )
    simulation: SimulationConfig = field(default_factory=SimulationConfig)
    geometry: GeometryConfig = field(default_factory=GeometryConfig)
    excitation: ExcitationConfig = field(default_factory=ExcitationConfig)
    camera: CameraConfig = field(default_factory=CameraConfig)
    noise: NoiseConfig = field(default_factory=NoiseConfig)
    processing: ProcessingConfig = field(default_factory=ProcessingConfig)

    def validate(self) -> None:
        """Ensure consistency across sub-configurations."""
        # Plate vs Inclusion checks
        if self.geometry.inclusion.center_x_mm > self.geometry.plate.length_mm or self.geometry.inclusion.center_x_mm < 0:
            raise ValueError("Inclusion x coordinate outside plate boundaries.")
        if self.geometry.inclusion.center_y_mm > self.geometry.plate.width_mm or self.geometry.inclusion.center_y_mm < 0:
            raise ValueError("Inclusion y coordinate outside plate boundaries.")
        if (self.geometry.inclusion.depth_mm + self.geometry.inclusion.thickness_mm) > self.geometry.plate.thickness_mm:
            raise ValueError(
                f"Inclusion depth ({self.geometry.inclusion.depth_mm} mm) + thickness "
                f"({self.geometry.inclusion.thickness_mm} mm) exceeds plate thickness "
                f"({self.geometry.plate.thickness_mm} mm)."
            )


def load_config(config_path: str | Path) -> LFMTConfig:
    """Load and parse YAML configuration file into a typed LFMTConfig."""
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found at: {path}")

    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    # Parse nested fields
    geo_raw = raw.get("geometry", {})
    plate_cfg = PlateConfig(**geo_raw.get("plate", {}))
    inc_cfg = InclusionConfig(**geo_raw.get("inclusion", {}))
    geometry = GeometryConfig(plate=plate_cfg, inclusion=inc_cfg)

    sim_cfg = SimulationConfig(**raw.get("simulation", {}))
    exc_cfg = ExcitationConfig(**raw.get("excitation", {}))
    cam_cfg = CameraConfig(**raw.get("camera", {}))
    noise_cfg = NoiseConfig(**raw.get("noise", {}))

    proc_raw = raw.get("processing", {})
    pct_cfg = PCTConfig(**proc_raw.get("pct", {}))
    spct_cfg = SPCTConfig(**proc_raw.get("spct", {}))
    rpt_cfg = RPTConfig(**proc_raw.get("rpt", {}))
    det_cfg = DetectionConfig(**proc_raw.get("detection", {}))
    mf_cfg = proc_raw.get("matched_filter", {"normalize": True, "zero_pad": True})

    proc_cfg = ProcessingConfig(
        pct=pct_cfg,
        spct=spct_cfg,
        rpt=rpt_cfg,
        matched_filter=mf_cfg,
        detection=det_cfg
    )

    proj_cfg = raw.get("project", {"name": "LFMT Slag Detection", "version": "0.1.0", "random_seed": 42})

    config = LFMTConfig(
        project=proj_cfg,
        simulation=sim_cfg,
        geometry=geometry,
        excitation=exc_cfg,
        camera=cam_cfg,
        noise=noise_cfg,
        processing=proc_cfg
    )
    config.validate()
    return config
