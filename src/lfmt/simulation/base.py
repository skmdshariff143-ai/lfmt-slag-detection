"""
Abstract base class and data structures for 3D thermal simulation backends.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Tuple
import numpy as np

from lfmt.config import LFMTConfig
from lfmt.materials import Material


@dataclass
class GroundTruth:
    """
    Exact ground-truth geometric defect parameters.
    """
    center_x_mm: float
    center_y_mm: float
    depth_mm: float
    diameter_mm: float
    thickness_mm: float
    material_name: str
    area_mm2: float
    volume_mm3: float
    has_defect: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "center_x_mm": self.center_x_mm,
            "center_y_mm": self.center_y_mm,
            "depth_mm": self.depth_mm,
            "diameter_mm": self.diameter_mm,
            "thickness_mm": self.thickness_mm,
            "material_name": self.material_name,
            "area_mm2": self.area_mm2,
            "volume_mm3": self.volume_mm3,
            "has_defect": self.has_defect,
        }


@dataclass
class SimulationResult:
    """
    Output container for 3D transient thermal simulation.

    Attributes:
        surface_temperature: 3D array of surface temperatures T(time, ny, nx) [K].
        time_vector: 1D temporal array t [s].
        x_grid_mm: 1D x-coordinate grid [mm].
        y_grid_mm: 1D y-coordinate grid [mm].
        z_grid_mm: 1D z-coordinate (depth) grid [mm].
        ground_truth: GroundTruth defect object.
        backend_name: Name of the solver used ("finite_difference" or "fem").
        metadata: Detailed runtime, mesh, and solver parameters.
        full_volume_temperature: Optional 4D volume array T(time, nz, ny, nx) [K].
    """
    surface_temperature: np.ndarray  # shape: (n_times, ny, nx)
    time_vector: np.ndarray          # shape: (n_times,)
    x_grid_mm: np.ndarray            # shape: (nx,)
    y_grid_mm: np.ndarray            # shape: (ny,)
    z_grid_mm: np.ndarray            # shape: (nz,)
    ground_truth: GroundTruth
    backend_name: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    full_volume_temperature: Optional[np.ndarray] = None


class ThermalSimulationBackend(ABC):
    """
    Abstract thermal solver interface.
    Polymorphic base allowing seamless switching between FEM and FDM.
    """

    @property
    @abstractmethod
    def backend_type(self) -> str:
        """Returns the canonical backend name (e.g. 'fem' or 'finite_difference')."""
        pass

    @property
    @abstractmethod
    def is_fem(self) -> bool:
        """Explicit boolean flag confirming if this is a genuine FEM solver."""
        pass

    @abstractmethod
    def run(self, config: LFMTConfig) -> SimulationResult:
        """
        Execute 3D transient heat simulation according to config.

        Args:
            config: Full LFMT configuration.

        Returns:
            SimulationResult containing surface thermal field and metadata.
        """
        pass
