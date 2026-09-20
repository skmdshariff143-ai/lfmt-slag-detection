"""
Configuration management system for LFMT slag detection framework.
Supports both V1 baseline parameters and Research V2 high-fidelity extensions.
"""

from __future__ import annotations
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
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
class WeldGeometryConfig:
    """Optional Weld & Heat Affected Zone (HAZ) geometric and material specification."""
    enabled: bool = False
    weld_bead_width_mm: float = 12.0
    weld_bead_thickness_mm: float = 0.5
    haz_width_mm: float = 4.0
    weld_centerline_x_mm: float = 50.0
    # Material properties (LITERATURE ASSUMED / PLACEHOLDERS)
    material_weld: str = "weld_metal_er70s"
    k_weld: Optional[float] = 48.0  # W/(m·K)
    rho_weld: Optional[float] = 7850.0 # kg/m³
    cp_weld: Optional[float] = 490.0  # J/(kg·K)
    material_haz: str = "haz_mild_steel"
    k_haz: Optional[float] = 45.0   # W/(m·K)
    rho_haz: Optional[float] = 7850.0  # kg/m³
    cp_haz: Optional[float] = 500.0   # J/(kg·K)


@dataclass
class ContactResistanceConfig:
    """Interfacial Thermal Contact Resistance between Steel Matrix and Slag Inclusion."""
    enabled: bool = False
    # Contact conductance h_c in W/(m²·K). Default 1e4 represents moderate contact; 1e6 is near-ideal.
    h_contact_w_m2k: float = 10000.0
    r_contact_m2k_w: Optional[float] = None  # Inverse of h_contact if specified


@dataclass
class InclusionConfig:
    shape: str = "cylinder"  # "cylinder", "ellipse", "strip", "irregular", "multi"
    center_x_mm: float = 50.0
    center_y_mm: float = 35.0
    depth_mm: float = 0.6
    diameter_mm: float = 8.0
    thickness_mm: float = 0.5
    material: str = "slag"
    thermal_conductivity: Optional[float] = None
    density: Optional[float] = None
    specific_heat: Optional[float] = None
    # Research V2 Geometry Attributes
    major_axis_mm: Optional[float] = None
    minor_axis_mm: Optional[float] = None
    orientation_deg: float = 0.0
    seed: int = 42
    inclusions_list: Optional[List[Dict[str, Any]]] = None  # Multi-inclusion list
    contact_resistance: ContactResistanceConfig = field(default_factory=ContactResistanceConfig)

    def __post_init__(self):
        if self.depth_mm < 0:
            raise ValueError(f"Inclusion depth must be >= 0, got {self.depth_mm}")
        if self.diameter_mm < 0 or self.thickness_mm <= 0:
            raise ValueError("Inclusion thickness must be strictly positive and diameter >= 0.")
        if self.major_axis_mm is None and self.diameter_mm > 0:
            self.major_axis_mm = self.diameter_mm
        if self.minor_axis_mm is None and self.diameter_mm > 0:
            self.minor_axis_mm = self.diameter_mm


@dataclass
class GeometryConfig:
    plate: PlateConfig = field(default_factory=PlateConfig)
    inclusion: InclusionConfig = field(default_factory=InclusionConfig)
    weld: WeldGeometryConfig = field(default_factory=WeldGeometryConfig)


@dataclass
class HeatingProfileConfig:
    """Excitation Spatial Heating Distribution."""
    type: str = "uniform"  # "uniform", "gaussian_centered", "gaussian_offaxis", "linear_gradient"
    center_x_mm: float = 50.0
    center_y_mm: float = 35.0
    sigma_x_mm: float = 30.0
    sigma_y_mm: float = 25.0
    gradient_slope_x: float = 0.0  # Fraction / mm across plate length


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
    heating_profile: HeatingProfileConfig = field(default_factory=HeatingProfileConfig)


@dataclass
class MeshRefinementConfig:
    """Non-uniform tensor / adaptive FEM mesh refinement specification."""
    mode: str = "uniform"  # "uniform", "adaptive_tensor", "coarse", "medium", "fine", "very_fine"
    target_elements_across_diameter: int = 8
    target_elements_through_depth: int = 4
    grading_factor: float = 1.3


@dataclass
class SimulationConfig:
    backend: str = "finite_difference"  # "fem" or "finite_difference"
    spatial_resolution: Dict[str, int] = field(
        default_factory=lambda: {"nx": 80, "ny": 56, "nz": 24}
    )
    timestep_s: float = 0.05
    total_time_s: float = 12.0
    mesh_refinement: MeshRefinementConfig = field(default_factory=MeshRefinementConfig)


@dataclass
class CameraConfig:
    resolution_x: int = 64
    resolution_y: int = 64
    sampling_rate_hz: float = 10.0
    lens_fov_mm: List[float] = field(default_factory=lambda: [100.0, 70.0])
    # Research V2 Realistic IR Camera Physics
    model_tier: str = "v1_ideal"  # "v1_ideal", "v2_realistic"
    netd_mK: float = 25.0  # Noise Equivalent Temperature Difference (mK)
    psf_sigma_px: float = 0.5  # Optical Point Spread Function blur width (pixels)
    integration_time_ms: float = 5.0
    adc_bits: int = 14  # Analog-to-Digital Converter quantization bits
    fpn_factor: float = 0.002  # Fixed Pattern Noise spatial gain nonuniformity
    drift_rate_k_per_s: float = 0.001  # Slow temporal sensor thermal drift
    emissivity_model: str = "simplified_kelvin_v1"  # "simplified_kelvin_v1" or "radiance_planck_v2"
    background_reflected_temp_k: float = 293.15


@dataclass
class NoiseConfig:
    preset: str = "CONTROLLED_AWGN"  # "IDEAL", "CONTROLLED_AWGN", "REALISTIC_CAMERA_NOISE"
    snr_db: Optional[float] = None  # None (clean), 30, 25, 20
    spatial_nonuniformity: float = 0.005
    emissivity_variation: float = 0.005
    seed: int = 42


@dataclass
class MaterialUncertaintyConfig:
    """Monte Carlo / Latin Hypercube Thermophysical Uncertainty Sampling."""
    enabled: bool = False
    k_slag_range: Tuple[float, float] = (1.0, 1.4)  # W/(m·K)
    rho_slag_range: Tuple[float, float] = (2600.0, 3000.0)  # kg/m³
    cp_slag_range: Tuple[float, float] = (750.0, 950.0)  # J/(kg·K)
    k_steel_range: Tuple[float, float] = (48.0, 55.0)  # W/(m·K)
    cp_steel_range: Tuple[float, float] = (460.0, 510.0)  # J/(kg·K)
    sampling_method: str = "latin_hypercube"  # "latin_hypercube" or "monte_carlo"
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
    matrix_type: str = "gaussian"  # "gaussian" or "sparse"


@dataclass
class DetectionConfig:
    threshold_method: str = "adaptive_otsu"
    morphology_kernel_size: int = 3
    min_area_px: int = 4
    multi_defect_mode: bool = False
    evaluation_tier: str = "tier_a"  # "tier_a" (Legacy V1), "tier_b" (Moderate), "tier_c" (Strict), "tier_d" (Ref)


@dataclass
class ProcessingConfig:
    pct: PCTConfig = field(default_factory=PCTConfig)
    spct: SPCTConfig = field(default_factory=SPCTConfig)
    rpt: RPTConfig = field(default_factory=RPTConfig)
    matched_filter: Dict[str, Any] = field(
        default_factory=lambda: {"normalize": True, "zero_pad": True, "use_delay_map": False}
    )
    detection: DetectionConfig = field(default_factory=DetectionConfig)


@dataclass
class LFMTConfig:
    project: Dict[str, Any] = field(
        default_factory=lambda: {"name": "LFMT Slag Detection", "version": "0.2.0-research-v2", "random_seed": 42}
    )
    simulation: SimulationConfig = field(default_factory=SimulationConfig)
    geometry: GeometryConfig = field(default_factory=GeometryConfig)
    excitation: ExcitationConfig = field(default_factory=ExcitationConfig)
    camera: CameraConfig = field(default_factory=CameraConfig)
    noise: NoiseConfig = field(default_factory=NoiseConfig)
    processing: ProcessingConfig = field(default_factory=ProcessingConfig)
    material_uncertainty: MaterialUncertaintyConfig = field(default_factory=MaterialUncertaintyConfig)

    def validate(self) -> None:
        """Ensure physical consistency across sub-configurations."""
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
    
    inc_dict = geo_raw.get("inclusion", {})
    contact_dict = inc_dict.pop("contact_resistance", {})
    contact_cfg = ContactResistanceConfig(**contact_dict)
    inc_cfg = InclusionConfig(contact_resistance=contact_cfg, **inc_dict)
    
    weld_cfg = WeldGeometryConfig(**geo_raw.get("weld", {}))
    geometry = GeometryConfig(plate=plate_cfg, inclusion=inc_cfg, weld=weld_cfg)

    sim_raw = raw.get("simulation", {})
    mesh_ref_raw = sim_raw.pop("mesh_refinement", {})
    mesh_ref_cfg = MeshRefinementConfig(**mesh_ref_raw)
    sim_cfg = SimulationConfig(mesh_refinement=mesh_ref_cfg, **sim_raw)

    exc_raw = raw.get("excitation", {})
    heating_raw = exc_raw.pop("heating_profile", {})
    heating_cfg = HeatingProfileConfig(**heating_raw)
    exc_cfg = ExcitationConfig(heating_profile=heating_cfg, **exc_raw)

    cam_cfg = CameraConfig(**raw.get("camera", {}))
    noise_cfg = NoiseConfig(**raw.get("noise", {}))
    mat_unc_cfg = MaterialUncertaintyConfig(**raw.get("material_uncertainty", {}))

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

    proj_cfg = raw.get("project", {"name": "LFMT Slag Detection", "version": "0.2.0-research-v2", "random_seed": 42})

    config = LFMTConfig(
        project=proj_cfg,
        simulation=sim_cfg,
        geometry=geometry,
        excitation=exc_cfg,
        camera=cam_cfg,
        noise=noise_cfg,
        processing=proc_cfg,
        material_uncertainty=mat_unc_cfg
    )
    config.validate()
    return config
