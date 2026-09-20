"""
Genuine 3-Dimensional Finite Element Method (FEM) Thermal Simulation Backend.

Formulates the 3-D weak variational form of the transient heat equation:
    \\int_\\Omega \\rho C_p \\frac{\\partial T}{\\partial t} v \\, d\\Omega
    + \\int_\\Omega k \\nabla T \\cdot \\nabla v \\, d\\Omega
    + \\int_{\\Gamma_{conv}} h T v \\, d\\Gamma
    = \\int_{\\Gamma_{front}} q(t) v \\, d\\Gamma
      + \\int_{\\Gamma_{conv}} h T_{amb} v \\, d\\Gamma

Discretization:
- Trilinear 8-node hexahedral finite elements (ElementHex1 on MeshHex)
- Spatially varying thermophysical material subdomains (Matrix Steel vs Slag Inclusion)
- Implicit Euler unconditionally stable time integration
- Sparse LU pre-factorization for high computational performance
- Front surface thermal extraction matching the standard SimulationResult contract.
"""

from __future__ import annotations
import math
import time
from typing import Dict, Any, Optional, Tuple
import numpy as np
import scipy.sparse.linalg as spla

try:
    from skfem import MeshHex, ElementHex1, Basis, FacetBasis, BilinearForm, LinearForm, asm
    from skfem.helpers import dot, grad
    SKFEM_AVAILABLE = True
except ImportError:
    SKFEM_AVAILABLE = False

from lfmt.config import LFMTConfig
from lfmt.materials import get_material, Material
from lfmt.excitation import LFMTExcitation
from lfmt.simulation.base import ThermalSimulationBackend, SimulationResult, GroundTruth


def _check_fem_engine() -> Tuple[bool, str]:
    """Check availability of external FEM solver engines."""
    if SKFEM_AVAILABLE:
        return True, "scikit-fem (3D Trilinear Hexahedral FEM)"
    return False, "None"


class FEMBackend(ThermalSimulationBackend):
    """
    Genuine 3-D Finite Element Method (FEM) Transient Heat Conduction Solver.
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
        Execute 3D FEM transient simulation using scikit-fem.
        """
        if not self._fem_available:
            msg = (
                "FEM Backend requested, but scikit-fem is not installed in the environment. "
                "To maintain research integrity, FDM will not be falsely labeled as FEM."
            )
            if self.fallback_if_unavailable:
                from lfmt.simulation.finite_difference import FiniteDifferenceBackend
                import warnings
                warnings.warn(msg + " Falling back to FiniteDifferenceBackend.", UserWarning)
                return FiniteDifferenceBackend().run(config)
            else:
                raise RuntimeError(msg)

        start_time = time.perf_counter()

        # 1. Geometry and Mesh Generation
        L_x = config.geometry.plate.length_mm * 1e-3  # [m]
        L_y = config.geometry.plate.width_mm * 1e-3   # [m]
        L_z = config.geometry.plate.thickness_mm * 1e-3 # [m]

        nx = config.simulation.spatial_resolution.get("nx", 40)
        ny = config.simulation.spatial_resolution.get("ny", 28)
        nz = config.simulation.spatial_resolution.get("nz", 12)

        x_nodes = np.linspace(0.0, L_x, nx + 1)
        y_nodes = np.linspace(0.0, L_y, ny + 1)
        z_nodes = np.linspace(0.0, L_z, nz + 1)

        mesh = MeshHex.init_tensor(x_nodes, y_nodes, z_nodes)
        basis = Basis(mesh, ElementHex1())

        # 2. Material Subdomains Definition
        mat_base = get_material(config.geometry.plate.material)
        mat_inc = get_material(config.geometry.inclusion.material)

        k_steel = mat_base.thermal_conductivity
        Cv_steel = mat_base.density * mat_base.specific_heat

        k_slag = mat_inc.thermal_conductivity
        Cv_slag = mat_inc.density * mat_inc.specific_heat

        inc = config.geometry.inclusion
        c_x = inc.center_x_mm * 1e-3
        c_y = inc.center_y_mm * 1e-3
        d_top = inc.depth_mm * 1e-3
        d_bottom = (inc.depth_mm + inc.thickness_mm) * 1e-3
        radius = (inc.diameter_mm / 2.0) * 1e-3

        # 3. Bilinear & Linear Variational Forms
        @BilinearForm
        def stiffness_form(u, v, w):
            dist_xy_sq = (w.x[0] - c_x)**2 + (w.x[1] - c_y)**2
            is_defect = (dist_xy_sq <= radius**2) & (w.x[2] >= d_top) & (w.x[2] <= d_bottom)
            k_val = np.where(is_defect, k_slag, k_steel)
            return k_val * dot(grad(u), grad(v))

        @BilinearForm
        def mass_form(u, v, w):
            dist_xy_sq = (w.x[0] - c_x)**2 + (w.x[1] - c_y)**2
            is_defect = (dist_xy_sq <= radius**2) & (w.x[2] >= d_top) & (w.x[2] <= d_bottom)
            Cv_val = np.where(is_defect, Cv_slag, Cv_steel)
            return Cv_val * u * v

        # Boundary Facet Bases
        h_conv = config.excitation.h_conv_w_m2k
        T_amb = config.excitation.ambient_temp_k

        facets_front = mesh.facets_satisfying(lambda x: np.isclose(x[2], 0.0))
        facets_all = mesh.boundary_facets()

        fbasis_front = FacetBasis(mesh, ElementHex1(), facets=facets_front)
        fbasis_all = FacetBasis(mesh, ElementHex1(), facets=facets_all)

        @BilinearForm
        def conv_boundary_form(u, v, w):
            return h_conv * u * v

        @LinearForm
        def front_flux_load(v, w):
            return 1.0 * v

        @LinearForm
        def amb_conv_load(v, w):
            return h_conv * T_amb * v

        # 4. Global FEM Matrix Assembly
        K = asm(stiffness_form, basis)
        M = asm(mass_form, basis)
        M_conv = asm(conv_boundary_form, fbasis_all)
        f_front_unit = asm(front_flux_load, fbasis_front)
        f_amb = asm(amb_conv_load, fbasis_all)

        # 5. Time Discretization & Solver Pre-factorization
        dt = config.simulation.timestep_s
        total_time = config.simulation.total_time_s

        exc = LFMTExcitation(
            f0_hz=config.excitation.f0_hz,
            f1_hz=config.excitation.f1_hz,
            duration_s=config.excitation.duration_s,
            q0_w_m2=config.excitation.q0_w_m2,
            sampling_rate_hz=1.0 / dt
        )
        t_out = exc.compute_time_vector(total_time)
        n_frames = len(t_out)

        # Implicit Euler system matrix: A = (1/dt)*M + K + M_conv
        A = (1.0 / dt) * M + K + M_conv
        A_csc = A.tocsc()
        solve_implicit_step = spla.factorized(A_csc)

        # 6. Extract front surface node indices for fast surface reconstruction
        # Front surface: z = 0
        front_node_mask = np.isclose(mesh.p[2], 0.0)
        front_node_indices = np.where(front_node_mask)[0]

        # Mesh coordinates for front surface
        x_pts = mesh.p[0, front_node_indices] * 1e3  # [mm]
        y_pts = mesh.p[1, front_node_indices] * 1e3  # [mm]

        # Sort coordinates into a structured (ny + 1, nx + 1) grid for camera interpolation
        # Unique sorted x and y coordinates
        x_unique_mm = np.unique(np.round(x_pts, 6))
        y_unique_mm = np.unique(np.round(y_pts, 6))
        
        # Build node index map for (ny+1, nx+1)
        grid_node_map = np.zeros((len(y_unique_mm), len(x_unique_mm)), dtype=int)
        for idx in front_node_indices:
            xi = np.argmin(np.abs(x_unique_mm - mesh.p[0, idx] * 1e3))
            yi = np.argmin(np.abs(y_unique_mm - mesh.p[1, idx] * 1e3))
            grid_node_map[yi, xi] = idx

        # Initial temperature vector
        T_vec = np.full(basis.N, T_amb, dtype=np.float64)
        surface_temp = np.zeros((n_frames, len(y_unique_mm), len(x_unique_mm)), dtype=np.float64)
        surface_temp[0, :, :] = T_vec[grid_node_map]

        # 7. Transient Time-Stepping Loop
        for frame_idx in range(1, n_frames):
            t_curr = t_out[frame_idx]
            q_flux = exc.heat_flux(t_curr)

            # RHS = (1/dt)*M*T^n + q(t)*f_front + f_amb
            rhs = (1.0 / dt) * (M @ T_vec) + q_flux * f_front_unit + f_amb
            T_vec = solve_implicit_step(rhs)

            surface_temp[frame_idx, :, :] = T_vec[grid_node_map]

        elapsed_s = time.perf_counter() - start_time

        area_mm2 = math.pi * (inc.diameter_mm / 2.0) ** 2
        volume_mm3 = area_mm2 * inc.thickness_mm
        gt = GroundTruth(
            center_x_mm=inc.center_x_mm,
            center_y_mm=inc.center_y_mm,
            depth_mm=inc.depth_mm,
            diameter_mm=inc.diameter_mm,
            thickness_mm=inc.thickness_mm,
            material_name=mat_inc.name,
            area_mm2=area_mm2,
            volume_mm3=volume_mm3,
            has_defect=True
        )

        metadata = {
            "solver": "FEMBackend (3D Finite Element Method)",
            "engine": "scikit-fem (Trilinear Hexahedral ElementHex1)",
            "is_fem": True,
            "dofs": basis.N,
            "elements": mesh.t.shape[1],
            "nodes": mesh.p.shape[1],
            "grid_size": [nz, ny, nx],
            "n_frames": n_frames,
            "dt_frame_s": dt,
            "time_integration": "Implicit Euler (Unconditionally Stable)",
            "runtime_seconds": elapsed_s,
        }

        z_unique_mm = np.unique(np.round(mesh.p[2] * 1e3, 6))

        return SimulationResult(
            surface_temperature=surface_temp,
            time_vector=t_out,
            x_grid_mm=x_unique_mm,
            y_grid_mm=y_unique_mm,
            z_grid_mm=z_unique_mm,
            ground_truth=gt,
            backend_name="fem",
            metadata=metadata
        )
