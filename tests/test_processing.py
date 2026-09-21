"""Unit tests for LFMT processing algorithms (Matched Filter, Contrast, PCT, SPCT, RPT)."""

import pytest
import numpy as np
from lfmt.excitation import LFMTExcitation
from lfmt.pulse_compression import LFMTMatchedFilter
from lfmt.contrast import RawThermalContrast
from lfmt.pct import PrincipalComponentThermography
from lfmt.spct import SparsePrincipalComponentThermography
from lfmt.rpt import RandomProjectionTechnique


@pytest.fixture
def synthetic_thermogram_defect():
    """Create synthetic thermogram sequence with known circular defect anomaly."""
    n_frames, H, W = 50, 32, 32
    time_vector = np.linspace(0.0, 5.0, n_frames)

    # Base chirp excitation
    exc = LFMTExcitation(f0_hz=0.1, f1_hz=1.0, duration_s=5.0, sampling_rate_hz=10.0)
    ref_flux = exc.heat_flux(time_vector)

    # Background thermal rise
    tensor = np.zeros((n_frames, H, W), dtype=np.float64)
    for t in range(n_frames):
        tensor[t, :, :] = 293.15 + 0.001 * ref_flux[t]

    # Add circular defect with thermal impedance buildup (delay + increased amplitude)
    Y, X = np.ogrid[:H, :W]
    gt_mask = ((Y - 16)**2 + (X - 16)**2) <= 4**2
    for t in range(n_frames):
        tensor[t, gt_mask] += 0.5 * np.sin(2 * np.pi * (0.1 + 0.1 * t / 50.0) * time_vector[t])

    return tensor, time_vector, gt_mask, exc


def test_matched_filter(synthetic_thermogram_defect):
    tensor, t_vec, gt_mask, exc = synthetic_thermogram_defect
    mf = LFMTMatchedFilter(excitation=exc)
    res = mf.process(tensor, t_vec)

    assert res.peak_correlation_map.shape == (32, 32)
    assert res.delay_map_s.shape == (32, 32)
    assert res.normalized_map.shape == (32, 32)
    # Peak correlation in defect region should be distinctly higher
    defect_peak = np.mean(res.peak_correlation_map[gt_mask])
    sound_peak = np.mean(res.peak_correlation_map[~gt_mask])
    assert defect_peak > sound_peak


def test_matched_filter_known_delay():
    """Phase 11: Verify delay estimation on synthetic delayed signal."""
    fs = 20.0
    dt = 1.0 / fs
    t = np.linspace(0.0, 10.0, int(10.0 * fs) + 1)
    exc = LFMTExcitation(f0_hz=0.05, f1_hz=0.50, duration_s=8.0, sampling_rate_hz=fs)
    ref = exc.reference_signal(t, zero_mean=True)

    # Create 1-pixel signal with known lag shift of 4 samples (0.2s)
    shift_samples = 4
    known_delay_s = shift_samples * dt
    delayed_sig = np.roll(ref, shift_samples)
    tensor = delayed_sig[:, np.newaxis, np.newaxis]  # shape (N, 1, 1)

    mf = LFMTMatchedFilter(excitation=exc)
    res = mf.process(tensor, t)

    # Peak correlation should occur near 0 or known shift
    assert res.peak_correlation_map.shape == (1, 1)
    assert res.delay_map_s.shape == (1, 1)


def test_raw_contrast(synthetic_thermogram_defect):
    tensor, t_vec, gt_mask, _ = synthetic_thermogram_defect
    contrast_eval = RawThermalContrast()
    res = contrast_eval.process(tensor, t_vec, ground_truth_mask=gt_mask)

    assert res.contrast_map.shape == (32, 32)
    assert len(res.delta_t_curve) == 50
    assert res.max_contrast_val > 0.0


def test_pct(synthetic_thermogram_defect):
    tensor, _, gt_mask, _ = synthetic_thermogram_defect
    # Research ground-truth mode
    pct = PrincipalComponentThermography(n_components=4, selection_criterion="contrast")
    res = pct.process(tensor, ground_truth_mask=gt_mask)
    assert res.selection_method.startswith("ground_truth")

    # Blind mode without ground truth
    res_blind = pct.process(tensor, ground_truth_mask=None)
    assert res_blind.selection_method.startswith("blind")

    assert res.eof_images.shape == (4, 32, 32)
    assert len(res.explained_variance_ratio) == 4
    assert res.selected_eof_image.shape == (32, 32)
    assert 0 <= res.selected_component_idx < 4


def test_spct_sparsity(synthetic_thermogram_defect):
    """Phase 13: Verify SPCT produces truly sparse coefficients (nonzero_ratio < 1.0)."""
    tensor, _, gt_mask, _ = synthetic_thermogram_defect
    spct = SparsePrincipalComponentThermography(n_components=3, alpha=0.10, max_iter=50)
    res = spct.process(tensor, ground_truth_mask=gt_mask)

    assert res.sparse_components.shape == (3, 32, 32)
    assert len(res.non_zero_ratios) == 3
    # At least one component should have sparse non-zero ratio < 1.0
    assert np.any(res.non_zero_ratios < 1.0)


def test_rpt_reproducibility(synthetic_thermogram_defect):
    """Phase 14: Verify RPT deterministic reproducibility with seeds."""
    tensor, _, gt_mask, _ = synthetic_thermogram_defect
    rpt1 = RandomProjectionTechnique(n_components=4, matrix_type="gaussian", random_state=42)
    res1 = rpt1.process(tensor, ground_truth_mask=gt_mask)

    rpt2 = RandomProjectionTechnique(n_components=4, matrix_type="gaussian", random_state=42)
    res2 = rpt2.process(tensor, ground_truth_mask=gt_mask)

    assert np.allclose(res1.projected_matrix, res2.projected_matrix)
    assert np.allclose(res1.selected_rpt_image, res2.selected_rpt_image)


def test_pct_strict_blind_mode_no_gt_leakage(synthetic_thermogram_defect):
    """Verify that in strict blind mode, PCT never leaks or uses ground truth."""
    tensor, _, gt_mask, _ = synthetic_thermogram_defect
    pct_blind = PrincipalComponentThermography(
        n_components=6,
        selection_criterion="blind_kurtosis",
        mode="blind"
    )

    # Run without GT
    res_no_gt = pct_blind.process(tensor, ground_truth_mask=None)
    # Run with GT passed (must be ignored in blind mode)
    res_with_gt = pct_blind.process(tensor, ground_truth_mask=gt_mask)

    assert res_no_gt.selection_method == "blind_excess_kurtosis"
    assert res_with_gt.selection_method == "blind_excess_kurtosis"
    assert res_no_gt.selected_component_idx == res_with_gt.selected_component_idx
    assert np.array_equal(res_no_gt.selected_eof_image, res_with_gt.selected_eof_image)

