"""
Simulation package: base abstractions, FDM and FEM backends.
"""

from lfmt.simulation.base import ThermalSimulationBackend, SimulationResult, GroundTruth
from lfmt.simulation.finite_difference import FiniteDifferenceBackend
from lfmt.simulation.fem import FEMBackend


def get_simulation_backend(name: str = "finite_difference") -> ThermalSimulationBackend:
    """
    Factory function to instantiate simulation backend.

    Args:
        name: "finite_difference" or "fem"
    """
    backend_key = name.lower().strip()
    if backend_key in ("finite_difference", "fdm", "fd"):
        return FiniteDifferenceBackend()
    elif backend_key in ("fem", "fenics", "sfepy"):
        return FEMBackend(fallback_if_unavailable=True)
    else:
        raise ValueError(f"Unknown simulation backend '{name}'. Supported: 'finite_difference', 'fem'")


__all__ = [
    "ThermalSimulationBackend",
    "SimulationResult",
    "GroundTruth",
    "FiniteDifferenceBackend",
    "FEMBackend",
    "get_simulation_backend",
]
