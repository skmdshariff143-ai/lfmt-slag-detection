r"""
High-Performance 3-Dimensional Finite Difference Method (FDM) Thermal Solver.

NOTE: This is a 3-D Finite Difference solver, explicitly labeled as FDM (not FEM).
Solves the heterogeneous transient heat conduction equation:
    \rho(x) C_p(x) \frac{\partial T}{\partial t} = \nabla \cdot (k(x) \nabla T)
with dynamic LFMT chirp surface flux and convective/radiative boundary conditions.
"""

from __future__ import annotations
import math
import time
from typing import Tuple, Dict, Any, Optional
import numpy as np

try:
    from numba import njit
    NUMBA_AVAILABLE = True
except ImportError:
    NUMBA_AVAILABLE = False

from lfmt.config import LFMTConfig
from lfmt.materials import get_material, Material
from lfmt.excitation import LFMTExcitation
from lfmt.simulation.base import ThermalSimulationBackend, SimulationResult, GroundTruth


if NUMBA_AVAILABLE:
    @njit(fastmath=True)
    def _fdm_step_kernel(
        T: np.ndarray,
        T_new: np.ndarray,
        k_x: np.ndarray,
        k_y: np.ndarray,
        k_z: np.ndarray,
        inv_Cv: np.ndarray,
        dx: float,
        dy: float,
        dz: float,
        dt_sub: float,
        q_flux: float,
        h_conv: float,
        T_amb: float,
        nz: int,
        ny: int,
        nx: int
    ) -> None:
        """Numba-accelerated 3D heterogeneous heat conduction stencil."""
        inv_dx2 = 1.0 / (dx * dx)
        inv_dy2 = 1.0 / (dy * dy)
        inv_dz2 = 1.0 / (dz * dz)

        for z in range(nz):
            for y in range(ny):
                for x in range(nx):
                    t_val = T[z, y, x]

                    # Conduction in X direction (harmonic mean fluxes)
                    if x > 0:
                        flux_x_m = k_x[z, y, x - 1] * (T[z, y, x - 1] - t_val) * inv_dx2
                    else:
                        flux_x_m = -h_conv * (t_val - T_amb) / dx

                    if x < nx - 1:
                        flux_x_p = k_x[z, y, x] * (T[z, y, x + 1] - t_val) * inv_dx2
                    else:
                        flux_x_p = -h_conv * (t_val - T_amb) / dx

                    # Conduction in Y direction
                    if y > 0:
                        flux_y_m = k_y[z, y - 1, x] * (T[z, y - 1, x] - t_val) * inv_dy2
                    else:
                        flux_y_m = -h_conv * (t_val - T_amb) / dy

                    if y < ny - 1:
                        flux_y_p = k_y[z, y, x] * (T[z, y + 1, x] - t_val) * inv_dy2
                    else:
                        flux_y_p = -h_conv * (t_val - T_amb) / dy

                    # Conduction in Z direction (Depth)
                    if z > 0:
                        flux_z_m = k_z[z - 1, y, x] * (T[z - 1, y, x] - t_val) * inv_dz2
                    else:
                        # Front heated surface: LFMT heat flux - convection
                        flux_z_m = (q_flux - h_conv * (t_val - T_amb)) / dz

                    if z < nz - 1:
                        flux_z_p = k_z[z, y, x] * (T[z + 1, y, x] - t_val) * inv_dz2
                    else:
                        # Rear surface: natural convection
                        flux_z_p = -h_conv * (t_val - T_amb) / dz

                    div_q = (flux_x_m + flux_x_p) + (flux_y_m + flux_y_p) + (flux_z_m + flux_z_p)
                    T_new[z, y, x] = t_val + dt_sub * inv_Cv[z, y, x] * div_q


def _numpy_fdm_step(
    T: np.ndarray,
    T_new: np.ndarray,
    k_x: np.ndarray,
    k_y: np.ndarray,
    k_z: np.ndarray,
    inv_Cv: np.ndarray,
    dx: float,
    dy: float,
    dz: float,
    dt_sub: float,
    q_flux: float,
    h_conv: float,
    T_amb: float,
    nz: int,
    ny: int,
    nx: int
) -> None:
    """Pure NumPy fallback 3D heat stencil."""
    inv_dx2 = 1.0 / (dx * dx)
    inv_dy2 = 1.0 / (dy * dy)
    inv_dz2 = 1.0 / (dz * dz)

    # Interior conduction
    flux_x_m = np.zeros_like(T)
    flux_x_p = np.zeros_like(T)
    flux_y_m = np.zeros_like(T)
    flux_y_p = np.zeros_like(T)
    flux_z_m = np.zeros_like(T)
    flux_z_p = np.zeros_like(T)

    # X-direction
    flux_x_m[:, :, 1:] = k_x[:, :, :-1] * (T[:, :, :-1] - T[:, :, 1:]) * inv_dx2
    flux_x_m[:, :, 0] = -h_conv * (T[:, :, 0] - T_amb) / dx
    flux_x_p[:, :, :-1] = k_x[:, :, :-1] * (T[:, :, 1:] - T[:, :, :-1]) * inv_dx2
    flux_x_p[:, :, -1] = -h_conv * (T[:, :, -1] - T_amb) / dx

    # Y-direction
    flux_y_m[:, 1:, :] = k_y[:, :-1, :] * (T[:, :-1, :] - T[:, 1:, :]) * inv_dy2
    flux_y_m[:, 0, :] = -h_conv * (T[:, 0, :] - T_amb) / dy
    flux_y_p[:, :-1, :] = k_y[:, :-1, :] * (T[:, 1:, :] - T[:, :-1, :]) * inv_dy2
    flux_y_p[:, -1, :] = -h_conv * (T[:, -1, :] - T_amb) / dy

    # Z-direction
    flux_z_m[1:, :, :] = k_z[:-1, :, :] * (T[:-1, :, :] - T[1:, :, :]) * inv_dz2
    flux_z_m[0, :, :] = (q_flux - h_conv * (T[0, :, :] - T_amb)) / dz
    flux_z_p[:-1, :, :] = k_z[:-1, :, :] * (T[1:, :, :] - T[:-1, :, :]) * inv_dz2
    flux_z_p[-1, :, :] = -h_conv * (T[-1, :, :] - T_amb) / dz

    div_q = (flux_x_m + flux_x_p) + (flux_y_m + flux_y_p) + (flux_z_m + flux_z_p)
    T_new[:] = T + dt_sub * inv_Cv * div_q


class FiniteDifferenceBackend(ThermalSimulationBackend):
    """
    Explicit 3-D Finite Difference Method (FDM) Simulation Backend.
    """

    @property
    def backend_type(self) -> str:
        return "finite_difference"

    @property
    def is_fem(self) -> bool:
        return False

    def run(self, config: LFMTConfig) -> SimulationResult:
        start_time = time.perf_counter()

        # Extract geometry & mesh
        L_x = config.geometry.plate.length_mm * 1e-3
        L_y = config.geometry.plate.width_mm * 1e-3
        L_z = config.geometry.plate.thickness_mm * 1e-3

        nx = config.simulation.spatial_resolution.get("nx", 80)
        ny = config.simulation.spatial_resolution.get("ny", 56)
        nz = config.simulation.spatial_resolution.get("nz", 24)

        dx = L_x / nx
        dy = L_y / ny
        dz = L_z / nz

        x_coords_mm = (np.arange(nx) + 0.5) * (dx * 1e3)
        y_coords_mm = (np.arange(ny) + 0.5) * (dy * 1e3)
        z_coords_mm = (np.arange(nz) + 0.5) * (dz * 1e3)

        # Materials
        mat_base = get_material(config.geometry.plate.material)
        mat_inc = get_material(config.geometry.inclusion.material)

        k_field = np.full((nz, ny, nx), mat_base.thermal_conductivity, dtype=np.float64)
        rho_field = np.full((nz, ny, nx), mat_base.density, dtype=np.float64)
        cp_field = np.full((nz, ny, nx), mat_base.specific_heat, dtype=np.float64)

        # Map inclusion into 3D grid
        inc = config.geometry.inclusion
        c_x = inc.center_x_mm * 1e-3
        c_y = inc.center_y_mm * 1e-3
        d_top = inc.depth_mm * 1e-3
        d_bottom = (inc.depth_mm + inc.thickness_mm) * 1e-3
        radius = (inc.diameter_mm / 2.0) * 1e-3

        # Grid mesh in meters
        X, Y, Z = np.meshgrid(
            (np.arange(nx) + 0.5) * dx,
            (np.arange(ny) + 0.5) * dy,
            (np.arange(nz) + 0.5) * dz,
            indexing="xy"
        )
        # Reorder to (nz, ny, nx)
        X = np.transpose(X, (2, 0, 1))
        Y = np.transpose(Y, (2, 0, 1))
        Z = np.transpose(Z, (2, 0, 1))

        # Cylindrical inclusion mask
        dist_xy_sq = (X - c_x) ** 2 + (Y - c_y) ** 2
        inc_mask = (dist_xy_sq <= radius ** 2) & (Z >= d_top) & (Z <= d_bottom)

        k_field[inc_mask] = mat_inc.thermal_conductivity
        rho_field[inc_mask] = mat_inc.density
        cp_field[inc_mask] = mat_inc.specific_heat

        # Heat capacity per unit volume Cv = rho * Cp
        Cv_field = rho_field * cp_field
        inv_Cv = 1.0 / Cv_field

        # Harmonic mean thermal conductivities across cell interfaces
        k_x = 2.0 * k_field[:, :, :-1] * k_field[:, :, 1:] / (k_field[:, :, :-1] + k_field[:, :, 1:] + 1e-12)
        k_y = 2.0 * k_field[:, :-1, :] * k_field[:, 1:, :] / (k_field[:, :-1, :] + k_field[:, 1:, :] + 1e-12)
        k_z = 2.0 * k_field[:-1, :, :] * k_field[1:, :, :] / (k_field[:-1, :, :] + k_field[1:, :, :] + 1e-12)

        # Excitation
        exc = LFMTExcitation(
            f0_hz=config.excitation.f0_hz,
            f1_hz=config.excitation.f1_hz,
            duration_s=config.excitation.duration_s,
            q0_w_m2=config.excitation.q0_w_m2,
            sampling_rate_hz=1.0 / config.simulation.timestep_s
        )
        total_time = config.simulation.total_time_s
        t_out = exc.compute_time_vector(total_time)
        n_frames = len(t_out)

        # Stability criterion for explicit FDM
        # dt_crit <= 0.45 / (alpha_max * (1/dx^2 + 1/dy^2 + 1/dz^2))
        alpha_max = max(mat_base.thermal_diffusivity, mat_inc.thermal_diffusivity)
        dt_crit = 0.40 / (alpha_max * (1.0 / (dx * dx) + 1.0 / (dy * dy) + 1.0 / (dz * dz)))
        
        dt_frame = config.simulation.timestep_s
        n_substeps = max(1, int(math.ceil(dt_frame / dt_crit)))
        dt_sub = dt_frame / n_substeps

        T_amb = config.excitation.ambient_temp_k
        h_conv = config.excitation.h_conv_w_m2k

        # Initial conditions: uniform ambient temperature
        T_curr = np.full((nz, ny, nx), T_amb, dtype=np.float64)
        T_next = np.full((nz, ny, nx), T_amb, dtype=np.float64)

        surface_temp = np.zeros((n_frames, ny, nx), dtype=np.float64)
        surface_temp[0, :, :] = T_curr[0, :, :]

        step_fn = _fdm_step_kernel if NUMBA_AVAILABLE else _numpy_fdm_step

        # Main temporal integration loop
        for frame_idx in range(1, n_frames):
            t_frame_start = t_out[frame_idx - 1]

            for sub in range(n_substeps):
                t_current = t_frame_start + sub * dt_sub
                q_flux = exc.heat_flux(t_current)

                step_fn(
                    T_curr,
                    T_next,
                    k_x,
                    k_y,
                    k_z,
                    inv_Cv,
                    dx,
                    dy,
                    dz,
                    dt_sub,
                    q_flux,
                    h_conv,
                    T_amb,
                    nz,
                    ny,
                    nx
                )
                # Swap buffers
                T_curr, T_next = T_next, T_curr

            # Record surface temperature (z = 0)
            surface_temp[frame_idx, :, :] = T_curr[0, :, :]

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
            "solver": "FiniteDifferenceBackend (3D FDM)",
            "is_fem": False,
            "grid_size": [nz, ny, nx],
            "cell_size_mm": [dz * 1e3, dy * 1e3, dx * 1e3],
            "n_frames": n_frames,
            "substeps_per_frame": n_substeps,
            "dt_sub_s": dt_sub,
            "dt_frame_s": dt_frame,
            "runtime_seconds": elapsed_s,
            "accelerator": "numba" if NUMBA_AVAILABLE else "numpy",
        }

        return SimulationResult(
            surface_temperature=surface_temp,
            time_vector=t_out,
            x_grid_mm=x_coords_mm,
            y_grid_mm=y_coords_mm,
            z_grid_mm=z_coords_mm,
            ground_truth=gt,
            backend_name="finite_difference",
            metadata=metadata
        )
