"""Pairing safeguards for conference analysis."""
import pandas as pd
import pytest

from scripts.analyze_detection_surface import analyze


def sample():
    return pd.DataFrame([
        dict(method=method, diameter_mm=4, depth_mm=.2, noise_condition="Clean",
             noise_seed=0, is_healthy=False, is_detected=True, iou=.5, cnr=2.)
        for method in ["A", "B"]
    ])


def test_identical_pairs_are_nonsignificant():
    surface, tests = analyze(sample())
    assert (surface.probability == 1).all()
    assert (tests.p_value == 1).all()
    assert (tests.p_holm == 1).all()


def test_duplicate_pair_is_rejected():
    frame = sample()
    with pytest.raises(ValueError, match="Duplicate"):
        analyze(pd.concat([frame, frame.iloc[:1]]))


def test_missing_match_is_rejected():
    frame = sample()
    frame.loc[1, "noise_seed"] = 1
    with pytest.raises(ValueError, match="Missing"):
        analyze(frame)
