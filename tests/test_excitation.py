"""Unit tests for LFMT chirp waveform generation and mathematical verification."""

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

    # Invalid: q0 < 0
    with pytest.raises(ValueError, match="Heat flux amplitude q0 must be >= 0"):
        LFMTExcitation(q0_w_m2=-100)

    # Invalid: Nyquist violation
    with pytest.raises(ValueError, match="below Nyquist limit"):
        LFMTExcitation(f0_hz=1.0, f1_hz=15.0, sampling_rate_hz=20.0)


def test_waveform_mathematical_properties():
    """Phase 10: Verify f(0)=f0, f(T)=f1, monotonic frequency sweep, non-negativity, reproducibility."""
    f0 = 0.05
    f1 = 0.50
    T_dur = 10.0
    q0 = 5000.0
    exc = LFMTExcitation(f0_hz=f0, f1_hz=f1, duration_s=T_dur, q0_w_m2=q0, sampling_rate_hz=20.0)
    t = exc.compute_time_vector(total_time_s=12.0)

    # 1. f(0) = f0
    f_inst = exc.instantaneous_frequency(t)
    assert np.isclose(f_inst[0], f0, atol=1e-6)

    # 2. f(T) = f1
    idx_T = np.argmin(np.abs(t - T_dur))
    assert np.isclose(f_inst[idx_T], f1, atol=1e-2)

    # 3. Monotonic frequency sweep during excitation [0, T]
    mask_active = (t >= 0) & (t <= T_dur)
    active_freqs = f_inst[mask_active]
    assert np.all(np.diff(active_freqs) >= 0.0)

    # 4. Nonnegative heat flux: q(t) >= 0 for all t
    flux = exc.heat_flux(t)
    assert np.all(flux >= 0.0)
    assert np.all(flux <= 2.0 * q0 + 1e-6)

    # 5. Reference signal normalization
    ref = exc.reference_signal(t, zero_mean=True)
    assert np.isclose(np.linalg.norm(ref), 1.0)

    # 6. Deterministic reproducibility
    t2, q2, f2, _ = generate_lfmt_waveform(f0_hz=f0, f1_hz=f1, duration_s=T_dur, q0_w_m2=q0, sampling_rate_hz=20.0, total_time_s=12.0)
    assert np.array_equal(t, t2)
    assert np.array_equal(flux, q2)
    assert np.array_equal(f_inst, f2)
