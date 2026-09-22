"""
Unit tests for MATLAB environment and capability detection.
"""

from lfmt.matlab.environment import detect_matlab_environment


def test_matlab_environment_detection():
    env = detect_matlab_environment()
    assert isinstance(env, dict)
    assert "matlab_available" in env
    assert "release" in env
    assert "matlab_engine_importable" in env
    assert "scientific_backend_status" in env
    
    if env["matlab_available"]:
        assert env["matlab_path"] is not None
        assert "R2026a" in env.get("release", "")
        assert env["scientific_backend_status"] == "MATLAB_CONSERVATIVE_FDM_AVAILABLE"
