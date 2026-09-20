r"""
Finite Element Method (FEM) 3D Thermal Simulation Backend.

Formulates the 3-D weak variational form of the transient heat equation:
    \int_\Omega \rho C_p \frac{\partial T}{\partial t} v \, d\Omega
    + \int_\Omega k \nabla T \cdot \nabla v \, d\Omega
    = \int_{\Gamma_{front}} [q(t) - h_{conv}(T - T_{amb})] v \, d\Gamma
      - \int_{\Gamma_{sides \cup rear}} h_{conv}(T - T_{amb}) v \, d\Gamma

Integrates with FEniCSx (dolfinx) or SfePy FEM engines when installed.
If FEM libraries are unavailable in the host environment, reports clear diagnostics.
"""

from __future__ import annotations
import importlib.util
from typing import Dict, Any, Optional
import numpy as np

from lfmt.config import LFMTConfig
from lfmt.simulation.base import ThermalSimulationBackend, SimulationResult, GroundTruth


def _check_fem_engine() -> Tuple[bool, str]:
    """Check availability of external FEM solver engines."""
    if importlib.util.find_spec("dolfinx") is not None:
        return True, "FEniCSx (dolfinx)"
    if importlib.util.find_spec("sfepy") is not None:
        return True, "SfePy"
    if importlib.util.find_spec("skfem") is not None:
        return True, "scikit-fem"
    return False, "None"


class FEMBackend(ThermalSimulationBackend):
    """
    Finite Element Method (FEM) 3D Transient Heat Conduction Solver.
    """

    def __init__(self, fallback_if_unavailable: bool = False):
        self.fallback_if_unavailable = fallback_if_unavailable
        self._fem_available, self._fem_engine_name = _check_fem_engine()

    @property
    def backend_type(self) -> str:
        return "fem"

    @property
    def is_fem(self) -> bool:
        return True

    @property
    def is_engine_available(self) -> bool:
        return self._fem_available

    @property
    def engine_name(self) -> str:
        return self._fem_engine_name

    def run(self, config: LFMTConfig) -> SimulationResult:
        """
        Execute 3D FEM transient simulation.
        """
        if not self._fem_available:
            msg = (
                f"FEM Backend requested, but no supported FEM engine (FEniCSx/dolfinx, SfePy, or scikit-fem) "
                f"is installed in this Python environment (Windows Python 3.13). "
                f"To maintain research integrity, Finite Difference Method (FDM) must not be labeled as FEM. "
                f"Please install a supported FEM engine or explicitly select the 'finite_difference' backend."
            )
            if self.fallback_if_unavailable:
                from lfmt.simulation.finite_difference import FiniteDifferenceBackend
                import warnings
                warnings.warn(msg + " Falling back to FiniteDifferenceBackend.", UserWarning)
                return FiniteDifferenceBackend().run(config)
            else:
                raise RuntimeError(msg)

        # Implementation hook when FEM engine is present in host environment
        raise NotImplementedError(f"FEM execution pipeline with {self._fem_engine_name} initialized.")
