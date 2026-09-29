"""Compute FDM material-assignment occupancy from the recorded comparison configs."""
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/conference/analysis/tier3"


def main():
    records = json.loads((OUT / "physics_manifest.json").read_text())["cases"]
    rows = []
    for record in records:
        cfg = record["config"]
        grid = cfg["simulation"]["spatial_resolution"]
        plate, inc = cfg["geometry"]["plate"], cfg["geometry"]["inclusion"]
        dx, dy, dz = plate["length_mm"] / grid["nx"], plate["width_mm"] / grid["ny"], plate["thickness_mm"] / grid["nz"]
        x = (np.arange(grid["nx"]) + .5) * dx - inc["center_x_mm"]
        y = (np.arange(grid["ny"]) + .5) * dy - inc["center_y_mm"]
        z = (np.arange(grid["nz"]) + .5) * dz
        xy = (y[:, None] ** 2 + x ** 2) <= (inc["diameter_mm"] / 2) ** 2
        inside_z = (z >= inc["depth_mm"]) & (z <= inc["depth_mm"] + inc["thickness_mm"])
        count = int(xy.sum() * inside_z.sum()) if inc["diameter_mm"] > 0 else 0
        target = np.pi * (inc["diameter_mm"] / 2) ** 2 * inc["thickness_mm"]
        rows.append(dict(diameter_mm=inc["diameter_mm"], depth_mm=inc["depth_mm"], nx=grid["nx"],
                         ny=grid["ny"], nz=grid["nz"], inclusion_cells=count,
                         represented_volume_mm3=count * dx * dy * dz, target_volume_mm3=target,
                         volume_error_pct=100 * abs(count * dx * dy * dz - target) / target if target else None))
    pd.DataFrame(rows).to_csv(OUT / "fdm_material_occupancy.csv", index=False)
    print(pd.DataFrame(rows).to_string(index=False))


if __name__ == "__main__":
    main()
