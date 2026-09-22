"""
Simulation Backend Factory for LFMT Research Platform (Research V3).
"""

from __future__ import annotations
from lfmt.simulation.base import ThermalSimulationBackend
from lfmt.simulation.fem import FEMBackend
from lfmt.simulation.matlab_backend import MATLABFDMBackend


class SimulationBackendFactory:
    """
    Factory for instantiating verified LFMT simulation backends.
    """

    @staticmethod
    def create(backend_name: str = "python_fem") -> ThermalSimulationBackend:
        """
        Instantiate backend by name:
          - 'python_fem' / 'fem': 3-D Trilinear Hexahedral FEM (scikit-fem)
          - 'matlab_fdm' / 'matlab': 3-D Conservative Finite Difference (MATLAB)
        """
        norm_name = backend_name.lower().strip()
        if norm_name in ("python_fem", "fem", "scikit_fem"):
            return FEMBackend()
        elif norm_name in ("matlab_fdm", "matlab", "matlab_engine", "matlab_batch"):
            return MATLABFDMBackend()
        else:
            raise ValueError(
                f"Unknown simulation backend: '{backend_name}'. "
                f"Available backends: ['python_fem', 'matlab_fdm']."
            )
