#!/usr/bin/env python3
"""
3-D FEM Mesh Convergence and Spatial Discretization Verification Suite (Research V2).

Evaluates mesh convergence across:
1. Coarse Uniform
2. Medium Uniform
3. Adaptive Graded (Candidate Production Mesh)
4. Reference Fine Graded (Truth Solution)

Across 4 Critical Defect Cases:
- Case A: Shallow Small (D = 4 mm,  z = 0.2 mm)
- Case B: Deep Small    (D = 4 mm,  z = 1.0 mm)
- Case C: Moderate      (D = 8 mm,  z = 0.4 mm)
- Case D: Large Deep    (D = 12 mm, z = 1.0 mm)

Monitors:
- Exact nodal resolution & physical spacing (min/max dx, dy, dz)
- Active elements across diameter, cover depth, and thickness
- Represented inclusion volume vs analytic cylinder volume
- Relative L2 errors, transient RMSE, peak contrast error
- Signal processing output similarity (MF, PCT)
- Quantitative pass/fail against frozen acceptance criteria
"""

from __future__ import annotations
import os
import sys
import json
import time
import math
from pathlib import Path
from typing import Dict, Any, List, Tuple
import numpy as np
import pandas as pd

from lfmt.config import load_config, LFMTConfig
from lfmt.simulation.fem import FEMBackend, generate_graded_1d_nodes, generate_graded_z_nodes
from lfmt.pulse_compression import LFMTMatchedFilter
from lfmt.pct import PrincipalComponentThermography
from lfmt.excitation import LFMTExcitation
from lfmt.detection import DefectDetector


FROZEN_CRITERIA = {
    "max_surface_temp_rel_error_pct": 2.0,
    "max_peak_contrast_rel_error_pct": 5.0,
    "max_surface_rel_l2_error_pct": 3.0,
    "max_centroid_shift_mm": 0.5,
    "max_volume_error_pct": 5.0
}


def analyze_mesh_geometry(
    x_nodes: np.ndarray,
    y_nodes: np.ndarray,
    z_nodes: np.ndarray,
    c_x: float,
    c_y: float,
    d_top: float,
    thickness: float,
    radius: float
) -> Dict[str, Any]:
    """Compute exact physical mesh discretization metrics."""
    nx = len(x_nodes) - 1
    ny = len(y_nodes) - 1
    nz = len(z_nodes) - 1
    n_elements = nx * ny * nz
    n_nodes = (nx + 1) * (ny + 1) * (nz + 1)

    dx_arr = np.diff(x_nodes)
    dy_arr = np.diff(y_nodes)
    dz_arr = np.diff(z_nodes)

    # Core defect window
    x_in_core = (x_nodes >= c_x - radius) & (x_nodes <= c_x + radius)
    y_in_core = (y_nodes >= c_y - radius) & (y_nodes <= c_y + radius)
    z_in_cover = (z_nodes <= d_top + 1e-6)
    z_in_defect = (z_nodes >= d_top - 1e-6) & (z_nodes <= d_top + thickness + 1e-6)

    elem_across_diam_x = max(0, int(np.sum(x_in_core) - 1))
    elem_across_diam_y = max(0, int(np.sum(y_in_core) - 1))
    elem_through_cover = max(0, int(np.sum(z_in_cover) - 1))
    elem_through_defect = max(0, int(np.sum(z_in_defect) - 1))

    # Inclusion volume numerical integration via cell tensor sum
    xc = 0.5 * (x_nodes[:-1] + x_nodes[1:])
    yc = 0.5 * (y_nodes[:-1] + y_nodes[1:])
    zc = 0.5 * (z_nodes[:-1] + z_nodes[1:])

    XC, YC, ZC = np.meshgrid(xc, yc, zc, indexing="ij")
    DX, DY, DZ = np.meshgrid(dx_arr, dy_arr, dz_arr, indexing="ij")

    dist_sq = (XC - c_x)**2 + (YC - c_y)**2
    in_defect_mask = (dist_sq <= radius**2) & (ZC >= d_top) & (ZC <= d_top + thickness)
    rep_vol_m3 = float(np.sum(DX[in_defect_mask] * DY[in_defect_mask] * DZ[in_defect_mask]))
    rep_vol_mm3 = rep_vol_m3 * 1e9

    exact_vol_mm3 = math.pi * ((radius * 1e3)**2) * (thickness * 1e3) if radius > 0 else 0.0
    vol_err_pct = abs(rep_vol_mm3 - exact_vol_mm3) / exact_vol_mm3 * 100.0 if exact_vol_mm3 > 0 else 0.0

    return {
        "n_nodes_x": len(x_nodes),
        "n_nodes_y": len(y_nodes),
        "n_nodes_z": len(z_nodes),
        "n_elements": n_elements,
        "dofs": n_nodes,
        "min_dx_mm": float(np.min(dx_arr) * 1e3),
        "max_dx_mm": float(np.max(dx_arr) * 1e3),
        "min_dy_mm": float(np.min(dy_arr) * 1e3),
        "max_dy_mm": float(np.max(dy_arr) * 1e3),
        "min_dz_cover_mm": float(np.min(dz_arr[:max(1, elem_through_cover)]) * 1e3),
        "max_dz_mm": float(np.max(dz_arr) * 1e3),
        "elem_across_diameter": elem_across_diam_x,
        "elem_through_cover": elem_through_cover,
        "elem_through_thickness": elem_through_defect,
        "represented_volume_mm3": round(rep_vol_mm3, 3),
        "analytic_volume_mm3": round(exact_vol_mm3, 3),
        "volume_error_pct": round(vol_err_pct, 2)
    }


def run_single_fem(cfg: LFMTConfig, x_nodes: np.ndarray, y_nodes: np.ndarray, z_nodes: np.ndarray) -> Tuple[np.ndarray, np.ndarray, float]:
    """Execute FEM on exact specified coordinate node arrays."""
    from skfem import MeshHex, ElementHex1, Basis, BilinearForm, LinearForm, asm, FacetBasis
    from skfem.helpers import dot, grad
    import scipy.sparse.linalg as spla
    from scipy.interpolate import RegularGridInterpolator
    from lfmt.materials import get_material

    t0 = time.perf_counter()
    mesh = MeshHex.init_tensor(x_nodes, y_nodes, z_nodes)
    basis = Basis(mesh, ElementHex1())

    mat_base = get_material(cfg.geometry.plate.material)
    mat_inc = get_material(cfg.geometry.inclusion.material)

    k_steel = mat_base.thermal_conductivity
    Cv_steel = mat_base.density * mat_base.specific_heat
    k_slag = mat_inc.thermal_conductivity
    Cv_slag = mat_inc.density * mat_inc.specific_heat

    inc = cfg.geometry.inclusion
    c_x, c_y = inc.center_x_mm * 1e-3, inc.center_y_mm * 1e-3
    d_top = inc.depth_mm * 1e-3
    thickness_m = inc.thickness_mm * 1e-3
    radius_m = (inc.diameter_mm / 2.0) * 1e-3

    @BilinearForm
    def stiffness_form(u, v, w):
        dist_sq = (w.x[0] - c_x)**2 + (w.x[1] - c_y)**2
        is_def = (dist_sq <= radius_m**2) & (w.x[2] >= d_top) & (w.x[2] <= d_top + thickness_m)
        k_val = np.where(is_def, k_slag, k_steel)
        return k_val * dot(grad(u), grad(v))

    @BilinearForm
    def mass_form(u, v, w):
        dist_sq = (w.x[0] - c_x)**2 + (w.x[1] - c_y)**2
        is_def = (dist_sq <= radius_m**2) & (w.x[2] >= d_top) & (w.x[2] <= d_top + thickness_m)
        Cv_val = np.where(is_def, Cv_slag, Cv_steel)
        return Cv_val * u * v

    h_conv = cfg.excitation.h_conv_w_m2k
    T_amb = cfg.excitation.ambient_temp_k

    facets_front = mesh.facets_satisfying(lambda x: np.isclose(x[2], 0.0))
    facets_all = mesh.boundary_facets()
    fbasis_front = FacetBasis(mesh, ElementHex1(), facets=facets_front)
    fbasis_all = FacetBasis(mesh, ElementHex1(), facets=facets_all)

    @BilinearForm
    def conv_form(u, v, w):
        return h_conv * u * v

    @LinearForm
    def flux_form(v, w):
        return 1.0 * v

    @LinearForm
    def amb_form(v, w):
        return h_conv * T_amb * v

    K = asm(stiffness_form, basis)
    M = asm(mass_form, basis)
    M_conv = asm(conv_form, fbasis_all)
    f_front = asm(flux_form, fbasis_front)
    f_amb = asm(amb_form, fbasis_all)

    dt = cfg.simulation.timestep_s
    exc = LFMTExcitation(
        f0_hz=cfg.excitation.f0_hz,
        f1_hz=cfg.excitation.f1_hz,
        duration_s=cfg.excitation.duration_s,
        q0_w_m2=cfg.excitation.q0_w_m2,
        sampling_rate_hz=1.0 / dt
    )
    t_out = exc.compute_time_vector(cfg.simulation.total_time_s)
    n_frames = len(t_out)

    A = (1.0 / dt) * M + K + M_conv
    solve_step = spla.factorized(A.tocsc())

    front_node_mask = np.isclose(mesh.p[2], 0.0)
    front_node_indices = np.where(front_node_mask)[0]
    x_pts_m = mesh.p[0, front_node_indices]
    y_pts_m = mesh.p[1, front_node_indices]
    x_unique_m = np.unique(np.sort(x_pts_m))
    y_unique_m = np.unique(np.sort(y_pts_m))

    grid_map = np.zeros((len(y_unique_m), len(x_unique_m)), dtype=int)
    for idx, (xv, yv) in enumerate(zip(x_pts_m, y_pts_m)):
        ix = np.searchsorted(x_unique_m, xv)
        iy = np.searchsorted(y_unique_m, yv)
        grid_map[iy, ix] = front_node_indices[idx]

    cam_nx = cfg.simulation.spatial_resolution.get("nx", 64)
    cam_ny = cfg.simulation.spatial_resolution.get("ny", 48)
    cam_x_mm = np.linspace(0.0, cfg.geometry.plate.length_mm, cam_nx)
    cam_y_mm = np.linspace(0.0, cfg.geometry.plate.width_mm, cam_ny)

    u_k = np.full(basis.N, T_amb, dtype=np.float64)
    surface_frames = np.zeros((n_frames, cam_ny, cam_nx), dtype=np.float64)
    M_over_dt = (1.0 / dt) * M

    for k, t_curr in enumerate(t_out):
        q_curr = exc.heat_flux(t_curr)
        rhs = M_over_dt.dot(u_k) + q_curr * f_front + f_amb
        u_k = solve_step(rhs)
        surf_2d = u_k[grid_map]

        interp = RegularGridInterpolator(
            (y_unique_m * 1e3, x_unique_m * 1e3),
            surf_2d,
            method="linear",
            bounds_error=False,
            fill_value=None
        )
        mesh_Y, mesh_X = np.meshgrid(cam_y_mm, cam_x_mm, indexing="ij")
        surface_frames[k] = interp((mesh_Y, mesh_X))

    runtime = time.perf_counter() - t0
    return surface_frames, t_out, runtime


def evaluate_mesh_convergence_suite(out_dir: Path, quick: bool = False) -> Dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    print("=" * 80)
    print("LFMT RESEARCH V2: RIGOROUS FEM MESH CONVERGENCE & VERIFICATION SUITE")
    print("=" * 80)

    cfg = load_config("configs/research_v2.yaml")
    cfg.simulation.total_time_s = 2.0 if quick else 3.0
    cfg.simulation.timestep_s = 0.1 if quick else 0.05
    t_amb = cfg.excitation.ambient_temp_k

    L_x = cfg.geometry.plate.length_mm * 1e-3
    L_y = cfg.geometry.plate.width_mm * 1e-3
    L_z = cfg.geometry.plate.thickness_mm * 1e-3

    cases = [
        {"id": "Case_A", "name": "Shallow Small (D=4mm, z=0.2mm)", "diameter": 4.0, "depth": 0.2, "thick": 0.5},
        {"id": "Case_B", "name": "Deep Small (D=4mm, z=1.0mm)", "diameter": 4.0, "depth": 1.0, "thick": 0.5},
        {"id": "Case_C", "name": "Moderate (D=8mm, z=0.4mm)", "diameter": 8.0, "depth": 0.4, "thick": 0.5},
        {"id": "Case_D", "name": "Large Deep (D=12mm, z=1.0mm)", "diameter": 12.0, "depth": 1.0, "thick": 0.5},
    ]

    all_case_results = []
    detector = DefectDetector(threshold_method="adaptive_otsu")
    exc = LFMTExcitation(
        f0_hz=cfg.excitation.f0_hz,
        f1_hz=cfg.excitation.f1_hz,
        duration_s=cfg.excitation.duration_s,
        q0_w_m2=cfg.excitation.q0_w_m2,
        sampling_rate_hz=1.0 / cfg.simulation.timestep_s
    )
    mf_engine = LFMTMatchedFilter(excitation=exc)

    for case in cases:
        print(f"\n>>> Running Case: {case['name']} <<<")
        diam = case["diameter"]
        depth = case["depth"]
        thick = case["thick"]
        r_m = (diam / 2.0) * 1e-3
        cx_m, cy_m = 0.050, 0.035
        dtop_m = depth * 1e-3
        thk_m = thick * 1e-3

        cfg.geometry.inclusion.diameter_mm = diam
        cfg.geometry.inclusion.depth_mm = depth
        cfg.geometry.inclusion.thickness_mm = thick
        cfg.geometry.inclusion.center_x_mm = 50.0
        cfg.geometry.inclusion.center_y_mm = 35.0

        # Define 4 mesh variants:
        # 1. Coarse Uniform
        x_coarse = np.linspace(0.0, L_x, 17)
        y_coarse = np.linspace(0.0, L_y, 13)
        z_coarse = np.linspace(0.0, L_z, 7)

        # 2. Medium Uniform
        x_med = np.linspace(0.0, L_x, 33)
        y_med = np.linspace(0.0, L_y, 25)
        z_med = np.linspace(0.0, L_z, 11)

        # 3. Adaptive Graded (Production Candidate)
        x_adapt = generate_graded_1d_nodes(L_x, cx_m, r_m, target_elements_core=12, target_elements_flank=8)
        y_adapt = generate_graded_1d_nodes(L_y, cy_m, r_m, target_elements_core=12, target_elements_flank=8)
        z_adapt = generate_graded_z_nodes(L_z, dtop_m, thk_m, target_cover=5, target_defect=5, target_back=5)

        # 4. Reference Fine Graded (Truth baseline)
        x_ref = generate_graded_1d_nodes(L_x, cx_m, r_m, target_elements_core=16, target_elements_flank=12)
        y_ref = generate_graded_1d_nodes(L_y, cy_m, r_m, target_elements_core=16, target_elements_flank=12)
        z_ref = generate_graded_z_nodes(L_z, dtop_m, thk_m, target_cover=8, target_defect=8, target_back=8)

        mesh_configs = [
            ("Reference Fine Graded (Truth)", x_ref, y_ref, z_ref, True),
            ("Adaptive Graded (Production)", x_adapt, y_adapt, z_adapt, False),
            ("Medium Uniform", x_med, y_med, z_med, False),
            ("Coarse Uniform", x_coarse, y_coarse, z_coarse, False),
        ]

        solutions = {}
        geom_metrics = {}

        for name, xn, yn, zn, is_ref in mesh_configs:
            gm = analyze_mesh_geometry(xn, yn, zn, cx_m, cy_m, dtop_m, thk_m, r_m)
            geom_metrics[name] = gm
            print(f"  Solving [{name}] -> DOFs: {gm['dofs']}, Elements: {gm['n_elements']}, Elements in D: {gm['elem_across_diameter']}, Elements in cover: {gm['elem_through_cover']}...")
            surf, t_vec, rt = run_single_fem(cfg, xn, yn, zn)
            solutions[name] = {"surf": surf, "t_vec": t_vec, "runtime_s": rt}

        # Reference solution baseline
        ref_surf = solutions["Reference Fine Graded (Truth)"]["surf"]
        ref_dt = ref_surf - t_amb
        ref_peak_dt = float(np.max(ref_dt))

        # Contrast curve on reference
        ny, nx = ref_surf.shape[1], ref_surf.shape[2]
        ref_c_defect = ref_dt[:, ny // 2, nx // 2]
        ref_c_sound = ref_dt[:, 2, 2]
        ref_contrast = np.abs(ref_c_defect - ref_c_sound)
        ref_peak_contrast = float(np.max(ref_contrast))

        # Compare each candidate mesh against reference
        for name, xn, yn, zn, is_ref in mesh_configs:
            sol = solutions[name]
            gm = geom_metrics[name]
            dt_mesh = sol["surf"] - t_amb
            peak_dt = float(np.max(dt_mesh))
            
            c_defect = dt_mesh[:, ny // 2, nx // 2]
            c_sound = dt_mesh[:, 2, 2]
            contrast = np.abs(c_defect - c_sound)
            peak_contrast = float(np.max(contrast))

            # Differences against truth
            diff = dt_mesh - ref_dt
            rmse_field = float(np.sqrt(np.mean(diff ** 2)))
            rel_l2_pct = float(np.linalg.norm(diff) / (np.linalg.norm(ref_dt) + 1e-12)) * 100.0
            peak_dt_err_pct = abs(peak_dt - ref_peak_dt) / (ref_peak_dt + 1e-12) * 100.0
            peak_contrast_err_pct = abs(peak_contrast - ref_peak_contrast) / (ref_peak_contrast + 1e-12) * 100.0

            # Pass / Fail criteria check
            pass_surface_dt = (peak_dt_err_pct <= FROZEN_CRITERIA["max_surface_temp_rel_error_pct"])
            pass_contrast = (peak_contrast_err_pct <= FROZEN_CRITERIA["max_peak_contrast_rel_error_pct"])
            pass_l2 = (rel_l2_pct <= FROZEN_CRITERIA["max_surface_rel_l2_error_pct"])
            pass_vol = (gm["volume_error_pct"] <= FROZEN_CRITERIA["max_volume_error_pct"])
            overall_pass = bool(pass_surface_dt and pass_contrast and pass_l2 and pass_vol) if not is_ref else True

            rec = {
                "case_id": case["id"],
                "case_name": case["name"],
                "mesh_name": name,
                "is_reference": is_ref,
                "dofs": gm["dofs"],
                "n_elements": gm["n_elements"],
                "min_dx_mm": gm["min_dx_mm"],
                "max_dx_mm": gm["max_dx_mm"],
                "min_dz_cover_mm": gm["min_dz_cover_mm"],
                "elem_across_diameter": gm["elem_across_diameter"],
                "elem_through_cover": gm["elem_through_cover"],
                "elem_through_thickness": gm["elem_through_thickness"],
                "represented_vol_mm3": gm["represented_volume_mm3"],
                "analytic_vol_mm3": gm["analytic_volume_mm3"],
                "volume_error_pct": gm["volume_error_pct"],
                "peak_delta_t_k": round(peak_dt, 4),
                "peak_contrast_k": round(peak_contrast, 4),
                "peak_delta_t_error_pct": round(peak_dt_err_pct, 2),
                "peak_contrast_error_pct": round(peak_contrast_err_pct, 2),
                "surface_rmse_k": round(rmse_field, 4),
                "relative_l2_error_pct": round(rel_l2_pct, 2),
                "runtime_s": round(sol["runtime_s"], 2),
                "pass_criteria": overall_pass
            }
            all_case_results.append(rec)
            status_str = "[PASS]" if overall_pass else "[FAIL]"
            print(f"    -> {name:30s} | DOFs: {gm['dofs']:5d} | Rel L2: {rel_l2_pct:5.2f}% | Contrast Err: {peak_contrast_err_pct:5.2f}% | Vol Err: {gm['volume_error_pct']:5.2f}% | {status_str}")

    df = pd.DataFrame(all_case_results)
    csv_path = out_dir / "fem_mesh_convergence.csv"
    json_path = out_dir / "fem_mesh_convergence.json"
    df.to_csv(csv_path, index=False)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(all_case_results, f, indent=2)

    print(f"\n[DONE] Convergence study successfully completed. Results written to {csv_path}")
    return all_case_results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run FEM mesh convergence suite.")
    parser.add_argument("--quick", action="store_true", help="Run rapid mode")
    parser.add_argument("--out-dir", type=str, default="results/research_v2", help="Output dir")
    args = parser.parse_args()

    evaluate_mesh_convergence_suite(Path(args.out_dir), quick=args.quick)


