"""
Noise Injection & Degradation Models for Infrared Thermography (Research V2).

Supports:
- Additive White Gaussian Noise (AWGN) at specified SNR (30 dB, 25 dB, 20 dB)
- Post-injection measured SNR verification (baseline-subtracted AC power)
- Radiance-domain emissivity and surface reflections
- Physical Focal Plane Array (FPA) noise: NETD, Fixed-Pattern Noise, Optical PSF blur, ADC quantization, Sensor Drift
- Three clean presets: IDEAL, CONTROLLED_AWGN, REALISTIC_CAMERA_NOISE
- Fully deterministic reproducible seeding
"""

from __future__ import annotations
import math
from enum import Enum
from typing import Optional, Tuple, Union
import numpy as np
from scipy.ndimage import gaussian_filter

from lfmt.config import NoiseConfig, CameraConfig


class CameraNoisePreset(str, Enum):
    IDEAL = "IDEAL"
    CONTROLLED_AWGN = "CONTROLLED_AWGN"
    REALISTIC_CAMERA_NOISE = "REALISTIC_CAMERA_NOISE"


def add_thermal_camera_noise(
    tensor_k: np.ndarray,
    snr_db: Optional[float] = 30.0,
    preset: Union[CameraNoisePreset, str] = CameraNoisePreset.CONTROLLED_AWGN,
    emissivity: float = 0.95,
    emissivity_variation: float = 0.005,
    ambient_temp_k: float = 293.15,
    use_radiance_emissivity: bool = True,
    seed: int = 42
) -> Tuple[np.ndarray, float]:
    """
    Convenience wrapper to degrade thermal sequence and return (noisy_tensor, actual_snr_db).
    """
    preset_str = preset.value if isinstance(preset, CameraNoisePreset) else str(preset)
    noisy = tensor_k.copy()

    if preset_str != "IDEAL":
        if emissivity_variation > 0:
            if use_radiance_emissivity:
                noisy = add_radiance_emissivity_variation(
                    noisy,
                    base_emissivity=emissivity,
                    variation_std=emissivity_variation,
                    t_ambient_k=ambient_temp_k,
                    seed=seed
                )
            else:
                rng = np.random.default_rng(seed)
                H, W = noisy.shape[1], noisy.shape[2]
                emissivity_map = 1.0 + rng.normal(0.0, emissivity_variation, size=(1, H, W))
                noisy = noisy * emissivity_map

        if snr_db is not None:
            noisy = add_awgn_noise(noisy, snr_db=snr_db, seed=seed)

    actual_snr = measure_actual_snr_db(tensor_k, noisy)
    return noisy, actual_snr



def measure_actual_snr_db(clean_tensor: np.ndarray, noisy_tensor: np.ndarray) -> float:
    """
    Measure actual post-injection SNR in decibels on the baseline-subtracted dynamic AC signal.
    """
    # Dynamic AC signal power (subtract spatial-temporal mean to isolate modulation)
    clean_ac = clean_tensor - np.mean(clean_tensor)
    signal_power = np.mean(clean_ac ** 2)

    noise_residual = noisy_tensor - clean_tensor
    noise_power = np.mean(noise_residual ** 2)

    if noise_power < 1e-15:
        return float("inf")
    if signal_power < 1e-15:
        return 0.0

    return float(10.0 * np.log10(signal_power / noise_power))


def add_awgn_noise(
    tensor: np.ndarray,
    snr_db: float | None,
    seed: int | None = 42
) -> np.ndarray:
    """
    Inject Additive White Gaussian Noise (AWGN) based on signal AC dynamic power.
    """
    if snr_db is None:
        return tensor.copy()

    rng = np.random.default_rng(seed)
    # Calculate temporal AC signal variance across entire sequence
    clean_ac = tensor - np.mean(tensor)
    signal_power = np.mean(clean_ac ** 2)

    if signal_power < 1e-12:
        return tensor.copy()

    noise_power = signal_power / (10.0 ** (snr_db / 10.0))
    noise_std = math.sqrt(noise_power)

    noise = rng.normal(loc=0.0, scale=noise_std, size=tensor.shape)
    return tensor + noise


SIGMA_SB = 5.670374419e-8  # Stefan-Boltzmann constant [W/(m^2 K^4)]


def compute_broadband_radiance(
    true_surface_temperature_k: np.ndarray,
    emissivity: np.ndarray | float = 0.95,
    t_ambient_k: float = 293.15
) -> np.ndarray:
    """
    Compute total exitant broadband thermal radiance [W/m^2] under graybody assumption.
    Includes emitted thermal radiation and reflected ambient environmental radiation:
        L_meas = epsilon * sigma * T_surf^4 + (1 - epsilon) * sigma * T_amb^4
    """
    eps = np.asarray(emissivity, dtype=np.float64)
    T_surf = np.asarray(true_surface_temperature_k, dtype=np.float64)
    T_amb = float(t_ambient_k)
    return eps * SIGMA_SB * (T_surf ** 4) + (1.0 - eps) * SIGMA_SB * (T_amb ** 4)


def compute_apparent_blackbody_temperature(
    measured_radiance: Optional[np.ndarray] = None,
    true_surface_temperature_k: Optional[np.ndarray] = None,
    emissivity: np.ndarray | float = 0.95,
    t_ambient_k: float = 293.15
) -> np.ndarray:
    """
    Compute apparent blackbody temperature [K] measured by an uncalibrated radiometer (assuming epsilon=1).
        T_apparent = (L_meas / sigma)^0.25 = [epsilon * T_surf^4 + (1 - epsilon) * T_amb^4]^0.25
    Physical invariant: When T_surf == T_amb, T_apparent == T_amb regardless of emissivity.
    """
    if measured_radiance is not None:
        L = np.asarray(measured_radiance, dtype=np.float64)
        return (np.maximum(1e-12, L) / SIGMA_SB) ** 0.25

    if true_surface_temperature_k is None:
        raise ValueError("Either measured_radiance or true_surface_temperature_k must be provided")

    eps = np.asarray(emissivity, dtype=np.float64)
    T_surf = np.asarray(true_surface_temperature_k, dtype=np.float64)
    T_amb = float(t_ambient_k)

    rad_sum = eps * (T_surf ** 4) + (1.0 - eps) * (T_amb ** 4)
    return (np.maximum(1e-12, rad_sum)) ** 0.25


def compute_emissivity_corrected_temperature(
    apparent_blackbody_temp_k: np.ndarray,
    emissivity: np.ndarray | float = 0.95,
    t_ambient_k: float = 293.15
) -> np.ndarray:
    """
    Invert apparent radiometric temperature to retrieve true surface temperature [K]
    given known surface emissivity and ambient reflected temperature:
        T_corrected = [ (T_apparent^4 - (1 - epsilon) * T_amb^4) / epsilon ]^0.25
    """
    eps = np.maximum(1e-3, np.asarray(emissivity, dtype=np.float64))
    T_app = np.asarray(apparent_blackbody_temp_k, dtype=np.float64)
    T_amb = float(t_ambient_k)

    rad_diff = (T_app ** 4) - (1.0 - eps) * (T_amb ** 4)
    rad_corrected = np.maximum(1e-12, rad_diff / eps)
    return rad_corrected ** 0.25


def add_radiance_emissivity_variation(
    true_surface_temperature_k: np.ndarray,
    base_emissivity: float = 0.95,
    variation_std: float = 0.005,
    t_ambient_k: float = 293.15,
    seed: int | None = 42
) -> np.ndarray:
    """
    Apply physical broadband radiance-level emissivity variations (Stefan-Boltzmann model).
    Returns apparent blackbody temperature cube [K].
    """
    if variation_std <= 0.0 and base_emissivity >= 0.999:
        return true_surface_temperature_k.copy()

    rng = np.random.default_rng(seed)
    H, W = true_surface_temperature_k.shape[1], true_surface_temperature_k.shape[2]

    eps_map = np.clip(
        rng.normal(base_emissivity, variation_std, size=(1, H, W)),
        0.10,
        1.0
    )

    return compute_apparent_blackbody_temperature(
        true_surface_temperature_k=true_surface_temperature_k,
        emissivity=eps_map,
        t_ambient_k=t_ambient_k
    )


def add_realistic_fpa_camera_noise(
    tensor_k: np.ndarray,
    netd_k: float = 0.025,
    psf_sigma_px: float = 0.5,
    fpn_factor: float = 0.002,
    adc_bits: int = 14,
    drift_rate_k_per_s: float = 0.001,
    time_vector: Optional[np.ndarray] = None,
    seed: int | None = 42
) -> np.ndarray:
    """
    Simulate realistic Focal Plane Array (FPA) camera sensor physics:
    1. Optical PSF spatial blur (diffraction/defocus)
    2. Fixed-Pattern Noise (FPN) gain & offset spatial non-uniformity
    3. NETD Gaussian temporal noise
    4. Sensor drift across acquisition duration
    5. ADC bit depth quantization
    """
    rng = np.random.default_rng(seed)
    n_frames, H, W = tensor_k.shape
    noisy = tensor_k.copy()

    # 1. Optical PSF blur
    if psf_sigma_px > 0:
        for k in range(n_frames):
            noisy[k] = gaussian_filter(noisy[k], sigma=psf_sigma_px, mode="nearest")

    # 2. Fixed-Pattern Noise (FPN)
    if fpn_factor > 0:
        gain_fpn = 1.0 + rng.normal(0.0, fpn_factor, size=(1, H, W))
        offset_fpn = rng.normal(0.0, netd_k * 0.5, size=(1, H, W))
        noisy = noisy * gain_fpn + offset_fpn

    # 3. Temporal NETD Gaussian noise
    if netd_k > 0:
        temporal_noise = rng.normal(0.0, netd_k, size=noisy.shape)
        noisy = noisy + temporal_noise

    # 4. Slow temporal sensor drift
    if drift_rate_k_per_s > 0 and time_vector is not None:
        drift = (drift_rate_k_per_s * time_vector)[:, np.newaxis, np.newaxis]
        noisy = noisy + drift

    # 5. ADC Quantization
    if adc_bits > 0:
        t_min = np.min(noisy)
        t_max = np.max(noisy)
        span = max(1e-3, t_max - t_min)
        q_levels = 2 ** adc_bits
        noisy = t_min + np.round((noisy - t_min) / span * (q_levels - 1)) * (span / (q_levels - 1))

    return noisy


def apply_noise_pipeline(
    tensor: np.ndarray,
    config: NoiseConfig,
    camera_config: Optional[CameraConfig] = None,
    time_vector: Optional[np.ndarray] = None
) -> np.ndarray:
    """
    Execute configured noise degradation pipeline supporting V1 & Research V2 presets.
    """
    preset = getattr(config, "preset", "CONTROLLED_AWGN")

    if preset == "IDEAL":
        return tensor.copy()

    noisy = tensor.copy()

    # Emissivity degradation
    if config.emissivity_variation > 0:
        emissivity_model = getattr(camera_config, "emissivity_model", "simplified_kelvin_v1") if camera_config else "simplified_kelvin_v1"
        if emissivity_model == "radiance_planck_v2":
            noisy = add_radiance_emissivity_variation(
                noisy,
                base_emissivity=0.95,
                variation_std=config.emissivity_variation,
                seed=config.seed
            )
        else:
            rng = np.random.default_rng(config.seed)
            H, W = noisy.shape[1], noisy.shape[2]
            emissivity_map = 1.0 + rng.normal(0.0, config.emissivity_variation, size=(1, H, W))
            noisy = noisy * emissivity_map

    # Realistic Camera Noise Mode
    if preset == "REALISTIC_CAMERA_NOISE" and camera_config is not None:
        netd_k = getattr(camera_config, "netd_mK", 25.0) * 1e-3
        psf = getattr(camera_config, "psf_sigma_px", 0.5)
        fpn = getattr(camera_config, "fpn_factor", 0.002)
        bits = getattr(camera_config, "adc_bits", 14)
        drift = getattr(camera_config, "drift_rate_k_per_s", 0.001)

        noisy = add_realistic_fpa_camera_noise(
            noisy,
            netd_k=netd_k,
            psf_sigma_px=psf,
            fpn_factor=fpn,
            adc_bits=bits,
            drift_rate_k_per_s=drift,
            time_vector=time_vector,
            seed=config.seed
        )

    # AWGN Noise Injection
    if config.snr_db is not None:
        noisy = add_awgn_noise(
            noisy,
            snr_db=config.snr_db,
            seed=config.seed
        )

    return noisy

