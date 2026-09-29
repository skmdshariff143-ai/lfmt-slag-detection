"""
Unit tests for SimulationBackendFactory.
"""

import pytest
from lfmt.simulation.factory import SimulationBackendFactory
from lfmt.simulation.fem import FEMBackend
from lfmt.simulation.matlab_backend import MATLABFDMBackend


def test_factory_creation():
    fem = SimulationBackendFactory.create("python_fem")
    assert isinstance(fem, FEMBackend)
    assert fem.backend_type == "fem"
    assert fem.is_fem is True

    fdm = SimulationBackendFactory.create("matlab_fdm")
    assert isinstance(fdm, MATLABFDMBackend)
    assert fdm.backend_type == "matlab_fdm"
    assert fdm.is_fem is False  # Non-overclaiming guardrail


def test_factory_invalid_backend():
    with pytest.raises(ValueError, match="Unknown simulation backend"):
        SimulationBackendFactory.create("unsupported_backend_xyz")
