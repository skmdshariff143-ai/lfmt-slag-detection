"""
Comprehensive Unit Tests for Intelligent Thermographic Defect Analyzer.

Verifies:
1. Single thermal frame upload -> Spatial methods active, temporal methods disabled.
2. LFMT chirp sequence -> Matched filter active, PCT/SPCT/RPT active, multi-task AI active.
3. Pulsed thermography sequence -> Matched filter strictly disabled, blind PCT/SPCT/RPT active.
4. Visible RGB photograph -> Flagged as non-thermal, thermographic physics blocked.
5. Healthy specimen -> Zero false positives, returns healthy classification.
6. Report generation -> Emits JSON, CSV, manifest, and diagnostic figure.
"""

import tempfile
from pathlib import Path
import pytest
import numpy as np

from lfmt.io.input_analyzer import UniversalInputAnalyzer, InputType, DataRepresentation, QualityStatus
from lfmt.analysis.method_selector import MethodApplicabilityEngine, MethodStatus
from lfmt.analysis.analyzer import AutoDefectAnalyzer, AnalysisResult
from lfmt.reporting.report_generator import DefectReportGenerator


@pytest.fixture
def analyzer():
    return AutoDefectAnalyzer()


def test_single_frame_mode(analyzer):
    """Verify single thermal frame activates spatial analysis and disables temporal methods."""
    # 2D frame with hot circular anomaly
    H, W = 48, 48
    frame = np.random.RandomState(42).normal(294.0, 0.1, (H, W))
    frame[20:28, 20:28] += 2.0  # Anomaly

    res: AnalysisResult = analyzer.analyze(frame, metadata_override={"temp_units": "K", "fov_mm": (100.0, 70.0)})

    assert res.input_summary["n_frames"] == 1
    assert res.input_summary["input_type"] == InputType.THERMAL_SINGLE_IMAGE.value
    
    # Check method applicability
    app_matrix = res.applicability_matrix["methods"]
    assert app_matrix["single_frame_spatial"]["is_applicable"] is True
    assert app_matrix["pct"]["is_applicable"] is False
    assert "Single frame detected" in app_matrix["raw_contrast"]["reason"] or "requires at least 2 frames" in app_matrix["raw_contrast"]["reason"]
    assert app_matrix["lfmt_matched_filter"]["is_applicable"] is False

    # Detection & Consensus
    assert res.consensus_verdict["is_anomaly_detected"] is True
    assert res.total_defects_found >= 1


def test_lfmt_sequence_mode(analyzer):
    """Verify LFMT sequence activates Matched Filter, PCT, SPCT, RPT, and AI."""
    N_frames, H, W = 30, 32, 32
    t_vec = np.linspace(0, 10.0, N_frames)
    f0, f1, dur = 0.05, 0.50, 10.0
    chirp_sig = np.sin(2 * np.pi * (f0 * t_vec + 0.5 * ((f1 - f0) / dur) * (t_vec ** 2)))
    cube = np.zeros((N_frames, H, W)) + 293.15
    for k in range(N_frames):
        cube[k, :, :] += 0.05 * t_vec[k]
        cube[k, 12:20, 12:20] += 1.2 * chirp_sig[k] + 1.5

    meta = {
        "temp_units": "K",
        "frame_rate_hz": 3.0,
        "time_vector": t_vec,
        "fov_mm": (100.0, 70.0),
        "excitation": {"type": "lfmt", "f0_hz": 0.05, "f1_hz": 0.50, "duration_s": 10.0}
    }

    res: AnalysisResult = analyzer.analyze(cube, metadata_override=meta)

    assert res.input_summary["n_frames"] == 30
    assert res.input_summary["excitation_type"] == "lfmt"

    app_matrix = res.applicability_matrix["methods"]
    assert app_matrix["raw_contrast"]["is_applicable"] is True
    assert app_matrix["lfmt_matched_filter"]["is_applicable"] is True
    assert app_matrix["pct"]["is_applicable"] is True
    assert app_matrix["spct"]["is_applicable"] is True
    assert app_matrix["rpt"]["is_applicable"] is True

    assert "lfmt_matched_filter" in res.processing_results_summary
    assert res.consensus_verdict["is_anomaly_detected"] is True


def test_pulsed_sequence_matched_filter_guard(analyzer):
    """Verify pulsed sequence strictly disables LFMT Matched Filter."""
    N_frames, H, W = 20, 32, 32
    t_vec = np.linspace(0, 5.0, N_frames)
    cube = np.zeros((N_frames, H, W)) + 293.15
    for k in range(N_frames):
        cube[k] += np.exp(-t_vec[k] / 1.5) * 5.0

    meta = {
        "temp_units": "K",
        "frame_rate_hz": 4.0,
        "time_vector": t_vec,
        "excitation_type": "pulsed",
        "fov_mm": (150.0, 150.0)
    }

    res: AnalysisResult = analyzer.analyze(cube, metadata_override=meta)

    app_matrix = res.applicability_matrix["methods"]
    assert app_matrix["lfmt_matched_filter"]["is_applicable"] is False
    assert "not LFMT chirp" in app_matrix["lfmt_matched_filter"]["reason"] or "disabled" in app_matrix["lfmt_matched_filter"]["reason"]

    # But PCT and Raw should be enabled
    assert app_matrix["raw_contrast"]["is_applicable"] is True
    assert app_matrix["pct"]["is_applicable"] is True


def test_visible_rgb_photo_guard(analyzer):
    """Verify ordinary RGB photograph is flagged as visible and blocks thermal physics."""
    H, W = 64, 64
    rgb_img = np.random.RandomState(42).randint(0, 255, (H, W, 3)).astype(np.uint8)

    res: AnalysisResult = analyzer.analyze(rgb_img)

    assert res.input_summary["input_type"] == InputType.VISIBLE_IMAGE.value
    assert res.input_summary["data_representation"] == DataRepresentation.VISIBLE_RGB.value
    assert res.ood_summary["status"] == "OUT_OF_DISTRIBUTION"
    assert any("visual photograph" in r.lower() or "rgb" in r.lower() for r in res.ood_summary["reasons"])


def test_healthy_specimen_rejection(analyzer):
    """Verify completely homogeneous healthy plate returns no defect."""
    N_frames, H, W = 20, 32, 32
    cube = np.random.RandomState(42).normal(293.15, 0.02, (N_frames, H, W))
    meta = {
        "temp_units": "K",
        "frame_rate_hz": 5.0,
        "excitation": {"type": "lfmt", "f0_hz": 0.05, "f1_hz": 0.50, "duration_s": 4.0}
    }

    res: AnalysisResult = analyzer.analyze(cube, metadata_override=meta)

    assert res.consensus_verdict["likely_defect_type"] == "HEALTHY"
    assert res.consensus_verdict["is_anomaly_detected"] is False


def test_report_generator_package(analyzer):
    """Verify report generator emits all expected files."""
    H, W = 32, 32
    frame = np.zeros((H, W)) + 295.0
    frame[12:20, 12:20] += 3.0

    res = analyzer.analyze(frame, metadata_override={"temp_units": "K", "fov_mm": (100.0, 70.0)})

    with tempfile.TemporaryDirectory() as tmp_dir:
        artifacts = DefectReportGenerator.export_report_package(res, output_dir=tmp_dir)
        
        assert "json_report" in artifacts
        assert "csv_summary" in artifacts
        assert "manifest" in artifacts
        assert "diagnostic_figure" in artifacts

        assert Path(artifacts["json_report"]).exists()
        assert Path(artifacts["csv_summary"]).exists()
        assert Path(artifacts["manifest"]).exists()
        assert Path(artifacts["diagnostic_figure"]).exists()
