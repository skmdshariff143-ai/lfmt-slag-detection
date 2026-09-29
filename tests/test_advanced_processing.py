"""Analytical signal checks and learned inference isolation."""
import numpy as np
import pytest

from lfmt.advanced_processing import ThermalSignalReconstruction, ChirpPhaseFusion
from lfmt.ml.segmenter import TemporalPixelSegmenter, features


def test_tsr_recovers_power_law_log_derivative():
    t = np.linspace(0, 12, 121)
    cube = np.full((len(t), 4, 4), 293.15)
    cooling = t > 2
    cube[cooling] += (5 * (t[cooling] - 2) ** -.5)[:, None, None]
    result = ThermalSignalReconstruction(3).process(cube, t, 2.)
    assert np.allclose(result.channels, -.5, atol=1e-10)
    assert np.allclose(result.score_map, 0, atol=1e-10)
    assert result.valid_pixels.all()


def test_tsr_rejects_absent_cooling_and_masks_nonpositive_rise():
    cube = np.ones((30, 4, 4)) * 293.15
    t = np.arange(30) / 10
    with pytest.raises(ValueError, match="cooling"):
        ThermalSignalReconstruction().process(cube, t, 3.)
    result = ThermalSignalReconstruction().process(cube, t, 1.)
    assert not result.valid_pixels.any()
    assert not result.score_map.any()


def test_phase_recovers_delay_and_ignores_zero_drive():
    t = np.arange(1000) / 100
    frequency, phase = 1., .7
    reference = np.cos(2 * np.pi * frequency * t)
    cube = (293.15 + np.cos(2 * np.pi * frequency * t - phase))[:, None, None] * np.ones((1, 3, 3))
    engine = ChirpPhaseFusion()
    result = engine.process(cube, t, reference, np.array([frequency]))
    assert np.allclose(result.channels, -phase, atol=.002)
    assert np.max(result.score_map) < 1e-10
    empty = engine.process(cube, t, np.zeros_like(t), np.array([frequency]))
    assert not empty.valid_pixels.any()


def test_learned_model_training_roundtrip_and_spatial_equivariance(tmp_path):
    model = TemporalPixelSegmenter()
    cube = np.ones((16, 8, 8)) * 293.15
    cube[:, 2:5, 2:5] += np.linspace(0, 1, 16)[:, None, None]
    mask = np.zeros((8, 8))
    mask[2:5, 2:5] = 1
    with pytest.raises(ValueError, match="Train"):
        model.predict(cube)
    loss = model.fit(features(cube), mask.ravel(), epochs=100)
    assert loss[-1] < loss[0]
    path = tmp_path / "model.json"
    model.save(path)
    loaded = TemporalPixelSegmenter.load(path)
    assert np.array_equal(model.predict(cube), loaded.predict(cube))
    assert np.allclose(model.predict(cube[:, ::-1, :]), model.predict(cube)[::-1, :])


def test_extended_harness_preserves_classical_results():
    from scripts.run_conference_study import execute_processing_pipeline
    from lfmt.config import LFMTConfig
    from lfmt.simulation.base import GroundTruth

    times = np.linspace(0, 14, 141)
    cube = np.broadcast_to((293.15 + .2 * times)[:, None, None], (141, 16, 16)).copy()
    mask = np.zeros((16, 16), dtype=bool)
    mask[6:10, 6:10] = True
    cube[:, mask] += (.1 * times)[:, None]
    model = TemporalPixelSegmenter()
    model.fit(features(cube), mask.ravel().astype(float), epochs=10)
    gt = GroundTruth(50., 35., .4, 8., .5, "slag", 50., 25.)
    cfg = LFMTConfig()
    before = execute_processing_pipeline(cube, times, cfg, gt, mask)
    after = execute_processing_pipeline(cube, times, cfg, gt, mask, model)
    assert len(before) == 5 and len(after) == 8
    assert [m.method_name for m in after[-3:]] == ["TSR", "Chirp Phase Fusion", "Temporal Pixel Net"]
    assert [(m.iou, m.is_detected) for m in before] == [(m.iou, m.is_detected) for m in after[:5]]
