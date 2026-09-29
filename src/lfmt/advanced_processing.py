"""Experimental cooling TSR and frequency-domain chirp transfer-phase images."""
from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter

import numpy as np
from numpy.typing import NDArray

FloatArray = NDArray[np.float64]


@dataclass
class SignalImage:
    score_map: FloatArray
    channels: FloatArray
    valid_pixels: NDArray[np.bool_]
    runtime_seconds: float


def validate_sequence(cube: FloatArray, times: FloatArray) -> None:
    if cube.ndim != 3 or times.ndim != 1 or cube.shape[0] != times.size:
        raise ValueError("Expected cube (time, height, width) and matching time vector")
    if times.size < 4 or not np.isfinite(cube).all() or not np.isfinite(times).all():
        raise ValueError("Sequence must contain finite samples")
    if np.any(np.diff(times) <= 0):
        raise ValueError("Time samples must strictly increase")


class ThermalSignalReconstruction:
    """Fit log(delta T) vs log(time since heating ended), using cooling only.

    This is an empirical finite-heating cooling baseline, not a pulsed-heating
    depth inversion. Nonpositive temperature-rise pixels are excluded explicitly.
    """

    def __init__(self, degree: int = 4) -> None:
        if degree < 1 or degree > 8:
            raise ValueError("TSR degree must be between 1 and 8")
        self.degree = degree

    def process(self, cube: FloatArray, times: FloatArray, heating_end_s: float) -> SignalImage:
        start = perf_counter()
        validate_sequence(cube, times)
        keep = times > heating_end_s
        if np.count_nonzero(keep) < self.degree + 2:
            raise ValueError("TSR requires at least degree+2 post-heating cooling samples")
        log_t = np.log(times[keep] - heating_end_s)
        rise = cube[keep] - cube[0]
        valid = np.all(rise > 0, axis=0)
        flat = rise.reshape(rise.shape[0], -1)
        coefficients = np.zeros((self.degree + 1, flat.shape[1]))
        if valid.any():
            design = np.polynomial.polynomial.polyvander(log_t, self.degree)
            coefficients[:, valid.ravel()] = np.linalg.lstsq(design, np.log(flat[:, valid.ravel()]), rcond=None)[0]
        # First logarithmic derivative sampled throughout the cooling window.
        derivative = np.polynomial.polynomial.polyvander(log_t, self.degree - 1)
        channels = (derivative @ (coefficients[1:] * np.arange(1, self.degree + 1)[:, None])).reshape(rise.shape)
        score = np.zeros(cube.shape[1:])
        if valid.any():
            reference = np.median(channels[:, valid], axis=1)
            score[valid] = np.sqrt(np.mean((channels[:, valid] - reference[:, None]) ** 2, axis=0))
        return SignalImage(score, channels, valid, perf_counter() - start)


class ChirpPhaseFusion:
    """Windowed Fourier transfer phase relative to the measured/excitation drive.

    Resolves frequency bands over the whole chirp, not steady-state lock-in
    equilibria. Bands with negligible drive or response have zero weight.
    """

    def process(self, cube: FloatArray, times: FloatArray, reference: FloatArray,
                frequencies_hz: FloatArray) -> SignalImage:
        start = perf_counter()
        validate_sequence(cube, times)
        if reference.shape != times.shape or not np.isfinite(reference).all():
            raise ValueError("Reference must match finite time samples")
        if not np.allclose(np.diff(times), np.diff(times)[0], rtol=1e-5):
            raise ValueError("Uniform time sampling is required")
        nyquist = .5 / float(np.diff(times)[0])
        if frequencies_hz.size == 0 or np.any(frequencies_hz <= 0) or np.any(frequencies_hz >= nyquist):
            raise ValueError("Frequency bands must be positive and below Nyquist")
        design = np.column_stack([np.ones(times.size), times - times.mean()])
        data = cube.reshape(times.size, -1)
        detrended = data - design @ np.linalg.lstsq(design, data, rcond=None)[0]
        drive = reference - design @ np.linalg.lstsq(design, reference, rcond=None)[0]
        basis = np.exp(-2j * np.pi * frequencies_hz[:, None] * times) * np.hanning(times.size)
        response = basis @ detrended
        excitation = basis @ drive
        supported = np.abs(excitation) > max(float(np.max(np.abs(excitation))) * 1e-6, 1e-12)
        phase = np.zeros(response.shape)
        weights = np.zeros(response.shape)
        for i in range(frequencies_hz.size):
            if not supported[i]:
                continue
            phase[i] = np.angle(response[i] * np.conj(excitation[i]))
            amplitude = np.abs(response[i])
            valid_band = amplitude > max(float(amplitude.max()) * 1e-6, 1e-12)
            weights[i, valid_band] = amplitude[valid_band]
        # Circular distance avoids the -pi/+pi discontinuity during fusion.
        background = np.angle(np.sum(weights * np.exp(1j * phase), axis=1))
        distance = np.abs(np.angle(np.exp(1j * (phase - background[:, None]))))
        total = weights.sum(axis=0)
        fused = np.divide((weights * distance).sum(axis=0), total, out=np.zeros_like(total), where=total > 0)
        return SignalImage(fused.reshape(cube.shape[1:]), phase.reshape((-1, *cube.shape[1:])),
                           (total > 0).reshape(cube.shape[1:]), perf_counter() - start)
