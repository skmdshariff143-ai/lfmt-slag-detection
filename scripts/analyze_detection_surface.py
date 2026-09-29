"""Read-only analysis of the frozen benchmark; never regenerates historical results."""
from __future__ import annotations

import hashlib
import itertools
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "results/conference/final/raw_results_final.csv"
OUT = ROOT / "results/conference/analysis"
KEYS = ["diameter_mm", "depth_mm", "noise_condition", "noise_seed"]


def analyze(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    defects = frame.loc[~frame.is_healthy].copy()
    if defects.duplicated(["method", *KEYS]).any():
        raise ValueError("Duplicate paired observations")
    groups = ["method", "diameter_mm", "depth_mm"]
    pooled = defects.groupby(groups).is_detected.agg(["sum", "count", "mean"]).reset_index()
    pooled["noise_condition"] = "Pooled (1 clean + 30 noisy)"
    stratified = defects.groupby([*groups, "noise_condition"]).is_detected.agg(["sum", "count", "mean"]).reset_index()
    surface = pd.concat([pooled, stratified], ignore_index=True).rename(
        columns={"sum": "detections", "count": "n", "mean": "probability"})
    rows = []
    # Geometry-level means avoid treating repeated noise seeds as independent specimens.
    # Run-level tests are also exported, explicitly marked as clustered/exploratory.
    for metric in ["is_detected", "iou", "cnr"]:
        for condition in ["All", *sorted(defects.noise_condition.unique())]:
            subset = defects if condition == "All" else defects[defects.noise_condition == condition]
            pairs = subset.pivot(index=KEYS, columns="method", values=metric).astype(float)
            if pairs.isna().any().any():
                raise ValueError("Missing or nonfinite paired observations")
            for unit in ["paired_run_exploratory", "geometry_mean"]:
                values = pairs if unit == "paired_run_exploratory" else pairs.groupby(level=[0, 1]).mean()
                for a, b in itertools.combinations(values.columns, 2):
                    delta = values[a].to_numpy() - values[b].to_numpy()
                    if not np.isfinite(delta).all():
                        raise ValueError("Nonfinite paired difference")
                    stat, p = (0.0, 1.0) if np.all(delta == 0) else wilcoxon(
                        delta, zero_method="wilcox", alternative="two-sided", method="approx")
                    rows.append(dict(metric=metric, noise_condition=condition, unit=unit,
                                     method_a=a, method_b=b, n_pairs=len(delta),
                                     nonzero_pairs=int(np.count_nonzero(delta)), statistic=float(stat),
                                     p_value=float(p), mean_difference=float(delta.mean())))
    tests = pd.DataFrame(rows)
    tests["p_holm"] = np.nan
    for _, family in tests.groupby(["metric", "noise_condition", "unit"]):
        order = family.p_value.sort_values().index
        adjusted = np.maximum.accumulate(tests.loc[order, "p_value"].to_numpy() * np.arange(len(order), 0, -1))
        tests.loc[order, "p_holm"] = np.minimum(adjusted, 1)
    return surface, tests


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in SOURCE.parent.iterdir() if p.is_file()}
    frame = pd.read_csv(SOURCE)
    surface, tests = analyze(frame)
    expected = set(itertools.product([4., 6., 8., 10., 12.], [.2, .4, .6, .8, 1.]))
    for method, cells in surface[surface.noise_condition.str.startswith("Pooled")].groupby("method"):
        if set(zip(cells.diameter_mm, cells.depth_mm)) != expected or not (cells.n == 31).all():
            raise ValueError(f"Incomplete conference grid for {method}")
    surface.to_csv(OUT / "detection_probability.csv", index=False)
    tests.to_csv(OUT / "paired_wilcoxon.csv", index=False)
    methods = sorted(surface.method.unique())
    conditions = ["Pooled (1 clean + 30 noisy)", "Clean", "SNR 30 dB", "SNR 25 dB", "SNR 20 dB"]
    fig, axes = plt.subplots(len(conditions), len(methods), figsize=(18, 17), constrained_layout=True)
    fig.suptitle("Frozen benchmark: empirical detection fractions\n"
                 "Clean: n=1/cell; noisy: 10 labels/cell with identical recorded scores (not independent repeats)",
                 fontsize=13)
    for i, condition in enumerate(conditions):
        for j, method in enumerate(methods):
            table = surface[(surface.method == method) & (surface.noise_condition == condition)].pivot(
                index="depth_mm", columns="diameter_mm", values="probability")
            ax = axes[i, j]
            im = ax.imshow(table, vmin=0, vmax=1, cmap="viridis", aspect="auto")
            ax.set_xticks(range(len(table.columns)), [f"{v:g}" for v in table.columns])
            ax.set_yticks(range(len(table.index)), [f"{v:g}" for v in table.index])
            ax.set_title(f"{method}\n{condition}")
            ax.set_xlabel("Diameter (mm)")
            ax.set_ylabel("Depth (mm)")
            for (y, x), value in np.ndenumerate(table.to_numpy()):
                ax.text(x, y, f"{value:.0%}", ha="center", va="center", fontsize=8,
                        color="white" if value < .5 else "black")
    fig.colorbar(im, ax=axes, shrink=.6, label="Empirical detection fraction")
    fig.savefig(OUT / "detection_probability.png", dpi=160)
    plt.close(fig)
    healthy = frame[frame.is_healthy].groupby(["method", "noise_condition"]).is_false_positive.agg(["sum", "count", "mean"])
    healthy.to_csv(OUT / "healthy_false_alarms.csv")
    noisy = frame[(~frame.is_healthy) & (frame.noise_condition != "Clean")]
    independence = noisy.groupby(["method", "diameter_mm", "depth_mm", "noise_condition"])[
        ["is_detected", "iou", "cnr"]].nunique().reset_index()
    independence.to_csv(OUT / "seed_metric_uniqueness.csv", index=False)
    assert before == {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in SOURCE.parent.iterdir() if p.is_file()}
    (OUT / "analysis_manifest.json").write_text(json.dumps({
        "analysis_version": "1.0.0", "source_version": "2.1.0-final-audited", "frozen_sha256": before,
        "pair_keys": KEYS, "metrics": ["is_detected", "iou", "cnr"],
        "notes": "Two-sided asymptotic Wilcoxon; zeros discarded, all-zero pairs p=1. Holm across ten method pairs per metric/condition/unit. Geometry means are primary; run-level p-values are exploratory because seeds share specimens. Clean fractions have n=1 per cell, noisy n=10; pooled n=31 is protocol-weighted, not a population POD estimate."
    }, indent=2) + "\n", encoding="utf-8")
    print(f"Saved {len(surface)} surface cells and {len(tests)} paired tests; frozen SHA256 unchanged.")


if __name__ == "__main__":
    main()
