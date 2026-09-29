"""Registered FEM/FDM D=4 mm comparison; diagnostics, not experimental validation."""
from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from lfmt.camera import VirtualIRCamera
from lfmt.config import load_config
from lfmt.simulation import get_simulation_backend


def main() -> None:
    out = ROOT / "results/conference/analysis/tier3"
    out.mkdir(parents=True, exist_ok=True)
    cases = [(4., depth, "baseline") for depth in [.2, .4, .6, .8, 1.]]
    cases += [(8., .4, "baseline"), (0., 0., "baseline"), (4., .2, "refined"), (4., 1., "refined")]
    rows, provenance = [], []
    for diameter, depth, mesh in cases:
        cfg = load_config(ROOT / "configs/conference_v2_experimental.yaml")
        cfg.geometry.inclusion.diameter_mm = diameter
        cfg.geometry.inclusion.depth_mm = depth
        cfg.simulation.total_time_s = 4. # Match the legacy comparison window.
        cfg.simulation.spatial_resolution = ({"nx": 30, "ny": 22, "nz": 12} if mesh == "baseline"
                                              else {"nx": 40, "ny": 28, "nz": 16})
        captures, metadata = {}, {}
        for backend in ["fem", "fdm"]:
            cfg.simulation.backend = backend
            result = get_simulation_backend(backend).run(cfg)
            if backend == "fem" and result.backend_name != "fem":
                raise ValueError("FEM fallback is not a valid independent comparison")
            captures[backend] = VirtualIRCamera(cfg.camera).capture(result)
            metadata[backend] = result.metadata
        fem, fdm = captures["fem"], captures["fdm"]
        if fem.thermograms.shape != fdm.thermograms.shape or not np.allclose(fem.time_vector, fdm.time_vector):
            raise ValueError("Camera registration failed; never crop unlike grids")
        a, b = fem.thermograms, fdm.thermograms
        if not np.isfinite(a).all() or not np.isfinite(b).all():
            raise ValueError("Solver produced nonfinite temperature")
        difference = b - a
        ambient = cfg.excitation.ambient_temp_k
        # Same physical pixel coordinates in both camera captures.
        center_a = a[:, 16, 16] - a[:, 2, 2]
        center_b = b[:, 16, 16] - b[:, 2, 2]
        row = dict(diameter_mm=diameter, depth_mm=depth, mesh=mesh,
                   l2_kelvin_pct=float(100 * np.linalg.norm(difference) / np.linalg.norm(a)),
                   l2_celsius_pct=float(100 * np.linalg.norm(difference) / np.linalg.norm(a - 273.15)),
                   l2_temperature_rise_pct=float(100 * np.linalg.norm(difference) / np.linalg.norm(a - ambient)),
                   rmse_k=float(np.sqrt(np.mean(difference ** 2))),
                   max_absolute_error_k=float(np.max(np.abs(difference))),
                   fem_peak_contrast_k=float(np.max(np.abs(center_a))),
                   fdm_peak_contrast_k=float(np.max(np.abs(center_b))),
                   contrast_rmse_k=float(np.sqrt(np.mean((center_a - center_b) ** 2))),
                   nominal_elements_across_diameter=diameter / (100 / cfg.simulation.spatial_resolution["nx"]))
        rows.append(row)
        provenance.append(dict(config=asdict(cfg), backends=metadata))
        pd.DataFrame(rows).to_csv(out / "small_defect_fem_fdm.csv", index=False)
        print(json.dumps(row), flush=True)
    source_paths = [ROOT / "src/lfmt/simulation/fem.py", ROOT / "src/lfmt/simulation/finite_difference.py", Path(__file__)]
    (out / "physics_manifest.json").write_text(json.dumps(dict(
        cases=provenance, source_sha256={str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in source_paths},
        caveat="Numerical cross-check on common camera coordinates over first 4s. Uniform meshes do not resolve a 4mm inclusion adequately. Celsius/Kelvin norms include arbitrary offsets; rise and contrast diagnostics are primary."
    ), indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
