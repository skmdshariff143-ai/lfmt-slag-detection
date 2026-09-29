"""
Physics & Spatio-Temporal Thermal Feature Extraction Engine.

Computes physical heat-transfer parameters, thermal diffusion lengths,
temporal transient metrics, and 2D spatial morphology indicators.
"""

from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Tuple
import numpy as np
from scipy.ndimage import sobel, laplace


@dataclass
class PhysicsFeatures:
    """Calculated thermodynamic and diffusion parameters."""
    material_name: str
    thermal_conductivity_w_mk: float
    density_kg_m3: float
    specific_heat_j_kgk: float
    thermal_diffusivity_m2_s: float
    thermal_effusivity_w_s12_m2k: float
    f0_hz: Optional[float] = None
    f1_hz: Optional[float] = None
    diffusion_depth_f0_mm: Optional[float] = None
    diffusion_depth_f1_mm: Optional[float] = None
    theoretical_penetration_range_mm: Optional[Tuple[float, float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "material_name": self.material_name,
            "thermal_conductivity_w_mk": self.thermal_conductivity_w_mk,
            "density_kg_m3": self.density_kg_m3,
            "specific_heat_j_kgk": self.specific_heat_j_kgk,
            "thermal_diffusivity_m2_s": f"{self.thermal_diffusivity_m2_s:.3e}",
            "thermal_effusivity_w_s12_m2k": round(self.thermal_effusivity_w_s12_m2k, 1),
            "f0_hz": self.f0_hz,
            "f1_hz": self.f1_hz,
            "diffusion_depth_f0_mm": round(self.diffusion_depth_f0_mm, 2) if self.diffusion_depth_f0_mm else None,
            "diffusion_depth_f1_mm": round(self.diffusion_depth_f1_mm, 2) if self.diffusion_depth_f1_mm else None,
            "theoretical_penetration_range_mm": (
                [round(self.theoretical_penetration_range_mm[0], 2), round(self.theoretical_penetration_range_mm[1], 2)]
                if self.theoretical_penetration_range_mm else None
            ),
            "metadata": self.metadata
        }


@dataclass
class SpatioTemporalFeatures:
    """Extracted physical and statistical feature vector."""
    peak_delta_t_k: float
    min_delta_t_k: float
    mean_temp_k: float
    time_to_peak_s: float
    cooling_slope_k_per_s: float
    heating_slope_k_per_s: float
    temporal_variance: float
    temporal_skewness: float
    temporal_kurtosis: float
    spatial_gradient_mean: float
    spatial_gradient_max: float
    laplacian_variance: float
    spatial_entropy: float
    raw_feature_vector: np.ndarray

    def to_dict(self) -> Dict[str, Any]:
        return {
            "peak_delta_t_k": round(self.peak_delta_t_k, 3),
            "min_delta_t_k": round(self.min_delta_t_k, 3),
            "mean_temp_k": round(self.mean_temp_k, 3),
            "time_to_peak_s": round(self.time_to_peak_s, 3),
            "cooling_slope_k_per_s": round(self.cooling_slope_k_per_s, 4),
            "heating_slope_k_per_s": round(self.heating_slope_k_per_s, 4),
            "temporal_variance": round(self.temporal_variance, 4),
            "temporal_skewness": round(self.temporal_skewness, 4),
            "temporal_kurtosis": round(self.temporal_kurtosis, 4),
            "spatial_gradient_mean": round(self.spatial_gradient_mean, 4),
            "spatial_gradient_max": round(self.spatial_gradient_max, 4),
            "laplacian_variance": round(self.laplacian_variance, 4),
            "spatial_entropy": round(self.spatial_entropy, 4),
        }


class PhysicsFeatureEngine:
    """Computes thermodynamic, diffusion, and statistical features."""

    @staticmethod
    def compute_physics_context(
        material_name: str = "mild_steel",
        f0_hz: Optional[float] = 0.05,
        f1_hz: Optional[float] = 0.50,
        custom_props: Optional[Dict[str, float]] = None
    ) -> PhysicsFeatures:
        """Derive physical thermal diffusion properties."""
        from lfmt.materials import get_material

        try:
            mat = get_material(material_name)
            k = mat.thermal_conductivity
            rho = mat.density
            cp = mat.specific_heat
        except KeyError:
            props = custom_props or {}
            k = props.get("k", 51.9)
            rho = props.get("rho", 7850.0)
            cp = props.get("cp", 486.0)

        alpha = k / (rho * cp)
        effusivity = math.sqrt(k * rho * cp)

        mu_f0 = math.sqrt(alpha / (math.pi * f0_hz)) * 1e3 if (f0_hz and f0_hz > 0) else None
        mu_f1 = math.sqrt(alpha / (math.pi * f1_hz)) * 1e3 if (f1_hz and f1_hz > 0) else None

        depth_range = (min(mu_f0, mu_f1), max(mu_f0, mu_f1)) if (mu_f0 and mu_f1) else None

        return PhysicsFeatures(
            material_name=material_name,
            thermal_conductivity_w_mk=k,
            density_kg_m3=rho,
            specific_heat_j_kgk=cp,
            thermal_diffusivity_m2_s=alpha,
            thermal_effusivity_w_s12_m2k=effusivity,
            f0_hz=f0_hz,
            f1_hz=f1_hz,
            diffusion_depth_f0_mm=mu_f0,
            diffusion_depth_f1_mm=mu_f1,
            theoretical_penetration_range_mm=depth_range
        )

    @staticmethod
    def extract_spatiotemporal_features(
        cube: np.ndarray,
        time_vector: np.ndarray
    ) -> SpatioTemporalFeatures:
        """Extract multi-dimensional temporal and spatial statistics from thermal sequence or 2D image."""
        if cube.ndim == 2:
            cube = cube[np.newaxis, :, :]

        N_frames, H, W = cube.shape

        # Global temporal statistics
        mean_profile = np.mean(cube, axis=(1, 2))
        peak_idx = int(np.argmax(mean_profile))
        t_peak = float(time_vector[peak_idx]) if len(time_vector) > peak_idx else 0.0

        peak_dt = float(np.max(cube) - np.min(cube[0]))
        min_dt = float(np.min(cube) - np.min(cube[0]))
        mean_t = float(np.mean(cube))

        # Slopes
        if peak_idx > 0:
            dt_heat = max(1e-4, time_vector[peak_idx] - time_vector[0])
            heat_slope = float((mean_profile[peak_idx] - mean_profile[0]) / dt_heat)
        else:
            heat_slope = 0.0

        if peak_idx < N_frames - 1:
            dt_cool = max(1e-4, time_vector[-1] - time_vector[peak_idx])
            cool_slope = float((mean_profile[-1] - mean_profile[peak_idx]) / dt_cool)
        else:
            cool_slope = 0.0

        # Temporal higher-order moments
        temp_var = float(np.var(mean_profile))
        t_norm = (mean_profile - np.mean(mean_profile)) / (math.sqrt(temp_var) + 1e-12)
        skewness = float(np.mean(t_norm ** 3))
        kurtosis = float(np.mean(t_norm ** 4) - 3.0)

        # Spatial features on peak / representative frame
        peak_frame = cube[peak_idx]
        grad_x = sobel(peak_frame, axis=1)
        grad_y = sobel(peak_frame, axis=0)
        grad_mag = np.hypot(grad_x, grad_y)
        grad_mean = float(np.mean(grad_mag))
        grad_max = float(np.max(grad_mag))

        lap_img = laplace(peak_frame)
        lap_var = float(np.var(lap_img))

        # Spatial entropy
        hist, _ = np.histogram(peak_frame.ravel(), bins=32, density=True)
        hist = hist[hist > 0]
        entropy = float(-np.sum(hist * np.log2(hist)))

        # 14-element feature vector
        vec = np.array([
            peak_dt, min_dt, mean_t, t_peak, heat_slope, cool_slope,
            temp_var, skewness, kurtosis, grad_mean, grad_max, lap_var, entropy, float(N_frames)
        ], dtype=np.float64)

        return SpatioTemporalFeatures(
            peak_delta_t_k=peak_dt,
            min_delta_t_k=min_dt,
            mean_temp_k=mean_t,
            time_to_peak_s=t_peak,
            cooling_slope_k_per_s=cool_slope,
            heating_slope_k_per_s=heat_slope,
            temporal_variance=temp_var,
            temporal_skewness=skewness,
            temporal_kurtosis=kurtosis,
            spatial_gradient_mean=grad_mean,
            spatial_gradient_max=grad_max,
            laplacian_variance=lap_var,
            spatial_entropy=entropy,
            raw_feature_vector=vec
        )
