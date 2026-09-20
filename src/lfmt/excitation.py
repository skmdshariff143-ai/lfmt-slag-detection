"""
Linear Frequency-Modulated Thermography (LFMT) Excitation Waveform Module.

Provides mathematical generation and validation for chirp heat flux,
instantaneous frequency, phase progression, and reference matched-filter kernels.
"""

from __future__ import annotations
import math
from dataclasses import dataclass
from typing import Tuple, Dict, Any
import numpy as np


@dataclass(frozen=True)
class LFMTExcitation:
    """
    Linear Frequency-Modulated (Chirp) Thermal Excitation Parameters.

    Attributes:
        f0_hz: Initial start frequency in Hz. Must be > 0.
        f1_hz: Final end frequency in Hz. Must be > f0_hz.
        duration_s: Total excitation duration in seconds. Must be > 0.
        q0_w_m2: Baseline heat flux amplitude in W/m^2. Must be > 0.
        sampling_rate_hz: Temporal sampling rate in Hz. Must be > 0.
    """
    f0_hz: float = 0.05
    f1_hz: float = 0.50
    duration_s: float = 10.0
    q0_w_m2: float = 5000.0
    sampling_rate_hz: float = 20.0

    def __post_init__(self) -> None:
        """Validate physical and mathematical constraints."""
        if self.f0_hz <= 0:
            raise ValueError(f"Start frequency f0 must be > 0, got {self.f0_hz} Hz.")
        if self.f1_hz <= self.f0_hz:
            raise ValueError(f"End frequency f1 ({self.f1_hz} Hz) must be strictly greater than f0 ({self.f0_hz} Hz).")
        if self.duration_s <= 0:
            raise ValueError(f"Excitation duration must be > 0, got {self.duration_s} s.")
        if self.q0_w_m2 < 0:
            raise ValueError(f"Heat flux amplitude q0 must be >= 0, got {self.q0_w_m2} W/m^2.")
        if self.sampling_rate_hz <= 0:
            raise ValueError(f"Sampling rate must be > 0, got {self.sampling_rate_hz} Hz.")
        
        # Nyquist criterion check
        nyquist_freq = self.sampling_rate_hz / 2.0
        if self.f1_hz > nyquist_freq:
            raise ValueError(
                f"Sampling rate {self.sampling_rate_hz} Hz is below Nyquist limit "
                f"for highest chirp frequency {self.f1_hz} Hz (needs at least {2 * self.f1_hz} Hz)."
            )

    @property
    def chirp_rate_beta(self) -> float:
        r"""
        Chirp sweep rate \beta = (f_1 - f_0) / T_{duration} [Hz/s].
        """
        return (self.f1_hz - self.f0_hz) / self.duration_s

    def compute_time_vector(self, total_time_s: float | None = None) -> np.ndarray:
        """
        Generate temporal evaluation points array t [s].

        Args:
            total_time_s: Optional extended observation time (including cooling phase).
                          Defaults to excitation duration.
        """
        t_max = total_time_s if total_time_s is not None else self.duration_s
        num_points = int(round(t_max * self.sampling_rate_hz)) + 1
        return np.linspace(0.0, t_max, num_points, endpoint=True)

    def instantaneous_frequency(self, t: np.ndarray | float) -> np.ndarray | float:
        r"""
        Instantaneous chirp frequency f(t) = f_0 + \beta \cdot t [Hz].
        """
        t_arr = np.asarray(t)
        # For t > duration, frequency is 0 (excitation ended)
        f_inst = np.where(
            (t_arr >= 0) & (t_arr <= self.duration_s),
            self.f0_hz + self.chirp_rate_beta * t_arr,
            0.0
        )
        return float(f_inst) if np.ndim(t) == 0 else f_inst

    def instantaneous_phase(self, t: np.ndarray | float) -> np.ndarray | float:
        r"""
        Instantaneous chirp phase \phi(t) = 2\pi (f_0 t + 0.5 \beta t^2) [rad].
        """
        t_arr = np.asarray(t)
        t_clamped = np.clip(t_arr, 0.0, self.duration_s)
        phase = 2.0 * math.pi * (self.f0_hz * t_clamped + 0.5 * self.chirp_rate_beta * (t_clamped ** 2))
        return float(phase) if np.ndim(t) == 0 else phase

    def heat_flux(self, t: np.ndarray | float) -> np.ndarray | float:
        r"""
        Applied LFMT heat flux q(t) = q0 * (1 + sin(\phi(t))) for t in [0, duration_s], else 0.
        [W/m^2].
        """
        t_arr = np.asarray(t)
        phase = self.instantaneous_phase(t_arr)
        flux = np.where(
            (t_arr >= 0) & (t_arr <= self.duration_s),
            self.q0_w_m2 * (1.0 + np.sin(phase)),
            0.0
        )
        return float(flux) if np.ndim(t) == 0 else flux

    def reference_signal(self, t: np.ndarray, zero_mean: bool = True) -> np.ndarray:
        """
        Normalized reference waveform for matched filtering / pulse compression.
        
        Args:
            t: Time vector in seconds.
            zero_mean: If True, removes DC bias to correlate only the modulated AC component.

        Returns:
            Normalized reference 1D numpy array.
        """
        flux = self.heat_flux(t)
        # Extract only during excitation
        mask = (t >= 0) & (t <= self.duration_s)
        ref = np.zeros_like(flux)
        ref[mask] = flux[mask]
        
        if zero_mean and np.any(mask):
            ref[mask] = ref[mask] - np.mean(ref[mask])
        
        norm = np.linalg.norm(ref)
        if norm > 1e-12:
            ref = ref / norm
        return ref

    def to_dict(self) -> Dict[str, Any]:
        """Serialize configuration parameters."""
        return {
            "f0_hz": self.f0_hz,
            "f1_hz": self.f1_hz,
            "duration_s": self.duration_s,
            "q0_w_m2": self.q0_w_m2,
            "sampling_rate_hz": self.sampling_rate_hz,
            "chirp_rate_beta": self.chirp_rate_beta,
        }


def generate_lfmt_waveform(
    f0_hz: float = 0.05,
    f1_hz: float = 0.50,
    duration_s: float = 10.0,
    q0_w_m2: float = 5000.0,
    sampling_rate_hz: float = 20.0,
    total_time_s: float | None = None
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Convenience function to generate standard LFMT time vector, flux, frequency and phase.

    Returns:
        (t, q_flux, f_inst, phase) arrays.
    """
    excitation = LFMTExcitation(
        f0_hz=f0_hz,
        f1_hz=f1_hz,
        duration_s=duration_s,
        q0_w_m2=q0_w_m2,
        sampling_rate_hz=sampling_rate_hz
    )
    t = excitation.compute_time_vector(total_time_s)
    q = excitation.heat_flux(t)
    f = excitation.instantaneous_frequency(t)
    phi = excitation.instantaneous_phase(t)
    return t, q, f, phi
