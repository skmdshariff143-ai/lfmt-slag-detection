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


def test_raw_contrast(synthetic_thermogram_defect):
    tensor, t_vec, gt_mask, _ = synthetic_thermogram_defect
    contrast_eval = RawThermalContrast()
    res = contrast_eval.process(tensor, t_vec, ground_truth_mask=gt_mask)

    assert res.contrast_map.shape == (32, 32)
    assert len(res.delta_t_curve) == 50
    assert res.max_contrast_val > 0.0


def test_pct(synthetic_thermogram_defect):
    tensor, _, gt_mask, _ = synthetic_thermogram_defect
    pct = PrincipalComponentThermography(n_components=4, selection_criterion="contrast")
    res = pct.process(tensor, ground_truth_mask=gt_mask)

    assert res.eof_images.shape == (4, 32, 32)
    assert len(res.explained_variance_ratio) == 4
    assert res.selected_eof_image.shape == (32, 32)
    assert 0 <= res.selected_component_idx < 4


def test_spct(synthetic_thermogram_defect):
    tensor, _, gt_mask, _ = synthetic_thermogram_defect
    spct = SparsePrincipalComponentThermography(n_components=3, alpha=0.05, max_iter=30)
    res = spct.process(tensor, ground_truth_mask=gt_mask)

    assert res.sparse_components.shape == (3, 32, 32)
    assert len(res.non_zero_ratios) == 3
    assert res.selected_sparse_image.shape == (32, 32)


def test_rpt(synthetic_thermogram_defect):
    tensor, _, gt_mask, _ = synthetic_thermogram_defect
    rpt = RandomProjectionTechnique(n_components=4, matrix_type="gaussian")
    res = rpt.process(tensor, ground_truth_mask=gt_mask)

    assert res.projected_components.shape == (4, 32, 32)
    assert res.selected_rpt_image.shape == (32, 32)
    assert res.compression_ratio > 1.0
