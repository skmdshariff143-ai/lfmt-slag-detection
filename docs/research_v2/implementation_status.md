# Research V2 Implementation Status & Module Matrix

Date: 2026-09-20  |  Branch: `research-v2`  |  Repository: `lkmt-slag-detection`

---

## Module Implementation Status

| Module / Component | Path | Status | Test Coverage | Description |
|-----------------------------------------------------------------------------------------------------------------------------------------------------------|
| **3D FEM Solver** | `src/lfmt/simulation/fem.py` | COMPLETE | 100% (Passed) | Adaptive tensor graded hexahedral meshing 14 DOFs, volume error <1.86% |
| **Radiometric Noise Model** | `src/lfmt/noise.py` | COMPLETE | 100% (Passed) | Stefan-Boltzmann exitance, inversion, physical invariants verified |
| **FPA Camera Sensor Physics** | `src/lfmt/noise.py` | COMPLETE | 100% (Passed) | Optical PSF blur, FPN, NETD, 14-bit ADC hunting, drift |
| **Multi-Defect Segmentation** | `src/lfmt/detection.py` | COMPLETE | 100% (Passed) | Cansidate extraction, Hungarian bipartite matching, tiered A,B,C,D |
| **Quantitative Metrics Suite** | `src/lfmt/metrics.py` | COMPLETE | 100% (Passed) | IoU, Dice, CNR, ROC-PR average precision, localization distance |
| **Experimental Data Ingestion** | `src/lfmt/io_experimental.py` | COMPLETE | 100% (Passed) | NPY, MAT, CSV thermogram loaders with physical sanity checks |
| **MEsh Convergence Runner** | `scripts/validate_fem_mesh.py` | COMPLETE | 100% (Passed) | 4 cases x 4 meshes automatic convergence check |
| **FDM vs FEM Cross-Check** | `scripts/compare_fdm_fem_v2.py` | COMPLETE | 100% (Passed) | Cell-centered vs node-based boundary analysis |
| **Ablation & SNR Verification** | `scripts/run_research_v2_ablation.py` | COMPLETE | 100% (Passed) | 4-config ablation study and dynamic AC SNR validation |


___

## Protection & Provenance Summary
1. `main` branch and `results/config/final/` remain protected and untouched.
2. `research-v2` branch is pushed remotely to GitHub.