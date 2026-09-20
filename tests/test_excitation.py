"""Unit tests for LFMT chirp waveform generation."""

import pytest
import numpy as np
from lfmt.excitation import LFMTExcitation, generate_lfmt_waveform


def test_lfmt_excitation_validation():
    # Valid instance
    exc = LFMTExcitation(f0_hz=0.05, f1_hz=0.5, duration_s=10.0, q0_w_m2=5000.0, sampling_rate_hz=20.0)
    assert exc.chirp_rate_beta == (0.5 - 0.05) / 10.0

    # Invalid: f1 <= f0
    with pytest.raises(ValueError, match="strictly greater than f0"):
        LFMTExcitation(f0_hz=0.5, f1_hz=0.1)

    # Invalid: duration <= 0
    with pytest.raises(ValueError, match="duration must be > 0"):
        LFMTExcitation(f0_hz=0.1, f1_hz=0.5, duration_s=0.0)

    # Invalid: q0 <= 0
    with pytest.raises(ValueError, match="Heat flux amplitude q0 must be > 0"):
        LFMTExcitation(q0_w_m2=-100)

    # Invalid: Nyquist violation
    with pytest.raises(ValueError, match="below Nyquist limit"):
        LFMTExcitation(f0_hz=1.0, f1_hz=15.0, sampling_rate_hz=20.0)


def test_waveform_generation():
    exc = LFMTExcitation(f0_hz=0.1, f1_hz=1.0, duration_s=5.0, q0_w_m2=2000.0, sampling_rate_hz=20.0)
    t = exc.compute_time_vector(total_time_s=8.0)
    assert t[0] == 0.0
    assert np.isclose(t[-1], 8.0)

    f_inst = exc.instantaneous_frequency(t)
    assert np.isclose(f_inst[0], 0.1)
    # At t = 5.0s, f = 1.0
    idx_5s = np.argmin(np.abs(t - 5.0))
    assert np.isclose(f_inst[idx_5s], 1.0, atol=1e-2)
    # At t > 5s, excitation is off (0 Hz)
    idx_7s = np.argmin(np.abs(t - 7.0))
    assert f_inst[idx_7s] == 0.0

    flux = exc.heat_flux(t)
    assert np.all(flux >= 0.0)  # Heat flux is non-negative: q0*(1+sin) >= 0
    assert np.all(flux <= 2.0 * 2000.0 + 1e-6)

    ref = exc.reference_signal(t, zero_mean=True)
    assert np.isclose(np.linalg.norm(ref), 1.0)
