# Web Application Data Provenance Audit Matrix

**Repository:** `https://github.com/skmdshariff143-ai/lfmt-slag-detection`  
**Dataset Version:** `conference_2026_frozen_final`  
**Audit Status:** Fully Verified against `results/conference/final/`

---

## Data Pipeline Architecture

```
[Frozen Scientific Dataset] (results/conference/final/)
       │
       ▼ (scripts/export_web_results.py)
[Web CSV / JSON Staging] (web_data/ & web/public/data/)
       │
       ▼ (scripts/verify_web_data.py -> PASS)
[Next.js App Router Client & Server Components] (web/src/app/)
```

---

## Route & Component Provenance Table

| Page Route | UI Component / Section | Scientific Metric / Property | Frontend Source File | Scientific Authoritative Source | Transformation / Processing | Provenance Status |
|---|---|---|---|---|---|---|
| **`/`** (Home) | Standout Fact Cards | Top Detection Rate, Peak CNR, Min Loc Error, Min Latency | `web/public/data/summary_by_method.json` | `results/conference/final/summary_by_method_final.csv` | Dynamic sort & format (`formatPct`, `formatMetric`) | **PASS** |
| **`/`** (Home) | Multi-Method Comparison Table | `detection_rate`, `mean_cnr`, `mean_iou`, `mean_dice`, `mean_loc_error_detected_mm`, `mean_runtime_ms` | `web/public/data/summary_by_method.json` | `results/conference/final/summary_by_method_final.csv` | Direct mapping; `null` sanitized | **PASS** |
| **`/`** (Home) | Provenance Banner | `dataset_version`, `total_evaluations`, `solver_backend` | `web/public/data/manifest.json` | `results/conference/final/experiment_manifest_final.json` | Direct JSON load | **PASS** |
| **`/conference`** | Live Metric Grid & Overview | Method-specific detection rate, CNR, IoU, Loc Error | `web/public/data/summary_by_method.json`, `summary_by_noise.json` | `results/conference/final/summary_by_method_final.csv`, `summary_by_noise_final.csv` | Client state filtering by noise scenario | **PASS** |
| **`/results`** | Method Overview Table & Chart | Overall benchmark performance across 775 defect runs / method | `web/public/data/summary_by_method.json` | `results/conference/final/summary_by_method_final.csv` | Recharts bar chart & table | **PASS** |
| **`/results/depth`** | Depth Degradation Curves | `detection_rate`, `mean_cnr`, `mean_iou`, `mean_loc_error_detected_mm` vs Depth $z \in [0.2, 1.0]\text{ mm}$ | `web/public/data/summary_by_depth.json` | `results/conference/final/summary_by_depth_final.csv` | Grouped line chart vs depth | **PASS** |
| **`/results/diameter`** | Sizing Curves & Matrix | Detection rate vs diameter, $z_{\max}$ at $\text{Detection} \ge 80\%$ | `web/public/data/summary_by_diameter.json`, `max_detectable_depth.json` | `results/conference/final/summary_by_diameter_final.csv`, `max_detectable_depth_final.csv` | Recharts line chart & tabular matrix | **PASS** |
| **`/results/noise`** | Noise Robustness & Healthy Table | Performance vs AWGN (Clean, 30 dB, 25 dB, 20 dB); Specificity & FPR | `web/public/data/summary_by_noise.json`, `healthy_specificity.json` | `results/conference/final/summary_by_noise_final.csv`, `healthy_specificity_final.csv` | Multi-series noise trajectory & healthy control summary | **PASS** |
| **`/sensitivity`** | Sensitivity Bar Chart & Table | $\Delta T_{\text{surf,max}}$, $\Delta T_{\text{defect,max}}$, PCT CNR, Detection status across PDE variations | `web/public/data/sensitivity_summary.json` | `results/conference/final/sensitivity_final.csv` | Recharts bar chart & quantitative table | **PASS** |
| **`/validation`** | 3-D FEM vs 3-D FDM Table | Peak surface $T$, max absolute diff, relative $L_2$ error | Embedded numerical cross-validation data | `results/validation/fem_fdm_cross_validation.json` | Direct table presentation | **PASS** |
| **`/materials`** | Thermophysical Database | Thermal conductivity ($k$), density ($\rho$), specific heat ($C_p$), diffusivity ($\alpha$) | `web/public/data/manifest.json` | `results/conference/final/experiment_manifest_final.json` + `src/lfmt/materials/` | Direct material cards | **PASS** |
| **`/methodology`** | Mathematical Foundations | PDE diffusion equations, chirp flux, matched filter, SVD/PCA | Static KaTeX component | Scientific formulation (Carslaw & Jaeger, Maldague) | KaTeX Math typesetting | **PASS** |
| **`/explorer`** | Single-Case Inspector | Representative case metrics (IoU, Dice, Loc Error, CNR) across Clean, 30, 25, 20 dB | `web/public/cases/*.json` | `scripts/export_web_thermograms.py` (evaluated on FEM simulation cache) | Representative single-case comparison | **PASS** |
| **`/thermograms`** | Virtual Camera Scrubber | Frame time $t \in [0.0, 10.0]\text{ s}$, $T_{\min}, T_{\max}, T_{\text{mean}}$ telemetry HUD | `web/public/cases/*.json`, `public/thermograms/` | `data/generated/fem/` cached simulation matrices | 10-frame excitation sequence playback | **PASS** |
| **`/about`** | Capstone Context & Citation | Project scope, simulation disclaimer, BibTeX `@software` | Static component | Repository metadata | Text & code block presentation | **PASS** |
| **`/qr`** | Conference Quick Access | Portal & GitHub repository QR codes | `https://api.qrserver.com/` | Configured production URLs | Scalable QR SVG/PNG render | **PASS** |

---

## Data Consistency Guarantees

1. **Zero Runtime Scientific Computation:** No FEM/FDM solvers or signal processing filters run in the browser or on Vercel edge functions.
2. **Immutable Frozen Artifacts:** All metrics originate from `results/conference/final/raw_results_final.csv` and are verified by `scripts/verify_web_data.py`.
3. **Strict Blind Benchmark Integrity:** The primary benchmark strictly adheres to blind automated detection (no oracle component selection).
