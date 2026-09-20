# Conference Presentation Claims & Scientific Safety Guide

**Project:** Linear Frequency-Modulated Infrared Thermography for Subsurface Slag Inclusion Detection in Mild Steel  
**Target Venue:** IEEE / NDT International Conferences & Oral Presentations  
**Source of Truth:** Frozen Audited Benchmark (`results/conference/final/`, Commit `0469c2b`)

---

## 1. SAFE TO SAY (Audited, Mathematically Verified, Fully Supported)

| Claim Area | Exact Permissible Statement | Supporting Artifact / Verification |
| :--- | :--- | :--- |
| **Simulation Scale** | "Our computational benchmark evaluates **4,030 total runs** (3,875 defect runs across 25 geometries + 155 healthy control evaluations across 10 deterministic noise realizations)." | `raw_results_final.csv`, `audit_conference_results.py` |
| **Solvers Used** | "The forward heat transfer physics is modeled via a genuine 3-D Galerkin Finite Element Method (`scikit-fem`, `ElementHex1` hexahedra) with implicit Euler time integration, cross-validated against an independent 3-D Finite Difference solver." | `src/lfmt/simulation/fem_solver.py`, `results/validation/fem_fdm_cross_validation.json` |
| **Solver Agreement** | "FEM and FDM forward solvers agree within **< 0.25% relative $L_2$ error** across homogeneous and defective test plates." | `results/validation/fem_fdm_cross_validation.json` |
| **Matched Filter Performance** | "Matched filtering (pulse compression) achieved the highest overall blind detection rate (**33.2%** overall, **68.0%** clean, **44.0%** at 30 dB SNR) due to temporal cross-correlation processing gain under noise." | `summary_by_method_final.csv`, `summary_by_noise_final.csv` |
| **PCT Performance** | "Principal Component Thermography achieved the highest defect contrast (**mean CNR = 2.30**) and the lowest centroid localization error (**1.13 mm**) among successfully detected defect cases." | `summary_by_method_final.csv` |
| **RPT Performance** | "Random Projection Technique (RPT) provided the lowest latency among advanced transform-based methods (**1.82 ms**), outperforming Raw Contrast under noise while running ~7&times; faster than PCT." | `summary_by_method_final.csv` |
| **Raw Contrast Failure** | "Raw thermal contrast collapsed to **0.9% overall detection** (0.0% under AWGN $\le 30\text{ dB}$), proving that advanced temporal or subspace processing is strictly necessary for LFMT." | `summary_by_method_final.csv`, `summary_by_noise_final.csv` |
| **Anti-Leakage Protocol** | "All algorithms operated under **strict blind mode**: zero ground-truth defect coordinates, masks, or depths were provided to post-processing or segmentation algorithms." | `src/lfmt/experiments.py`, `docs/experiment_protocol.md` |
| **Healthy Specificity** | "PCT achieved **100.0% specificity (0.0% false alarm rate)** on healthy control specimens at nominal 30 dB SNR across all 10 random seeds." | `healthy_specificity_final.csv` |
| **Depth Limit** | "Under the evaluated excitation ($q_0 = 5000\text{ W/m}^2$, $0.05 \to 0.50\text{ Hz}$), defects at depths $z \le 0.4\text{ mm}$ are reliably detectable, whereas defects at $z \ge 0.8\text{ mm}$ require $D \ge 10\text{ mm}$ or high SNR." | `summary_by_depth_final.csv`, `max_detectable_depth_final.csv` |

---

## 2. NEEDS QUALIFICATION (Contextual, Condition-Dependent)

| Claim Area | Qualifying Language Required | Why Qualification is Essential |
| :--- | :--- | :--- |
| **"Validation"** | Say: *"Numerical cross-validation and physics sanity verification"* instead of *"Experimental validation"*. | All forward solutions are computational; physical infrared camera experiments on physical mild steel weld coupons represent essential future work. |
| **Healthy Specificity** | Say: *"PCT achieved 100% specificity specifically at 30 dB SNR; lower SNRs and uncalibrated thresholds produce false alarms on uniform plates."* | Do not claim "100% specificity across all conditions", because heavy noise on flat plates triggers false alarms without adaptive threshold calibration. |
| **Defect Geometry** | Say: *"Evaluated on representative cylindrical disc slag inclusions ($D \in 4\text{--}12\text{ mm}$, $z \in 0.2\text{--}1.0\text{ mm}$)."* | Real weld slag entrapped in SMAW/FCAW beads has irregular, non-canonical 3D morphologies. |
| **Material Properties** | Say: *"Thermophysical properties ($k, \rho, C_p$) were calibrated to verified experimental literature values (Incropera, Mills 1993)."* | Variations in mild steel composition and slag flux stoichiometry will slightly shift absolute thermal diffusion times in practice. |
| **Single-Case Views** | Say: *"Representative visualization case (deterministic visual seed 42)"* rather than *"General result"*. | Single-case explorer graphics illustrate mechanism; quantitative claims must cite the multi-seed 4,030-evaluation statistical aggregate. |

---

## 3. DO NOT SAY (Scientifically Inaccurate, Prohibited Claims)

| Prohibited Phrase | Why It Is False / Prohibited | Correct Alternative |
| :--- | :--- | :--- |
| ❌ *"We proved this system in field industry testing."* | **False:** No physical experiments were conducted in this phase. | ✅ *"We developed and numerically benchmarked a simulation framework for LFMT inspection feasibility."* |
| ❌ *"PCT is universally the best algorithm for thermography."* | **False:** Matched Filter achieved higher blind detection rate (33.2% vs 21.9%) under noise. | ✅ *"Matched Filter maximizes detection sensitivity under noise, while PCT optimizes contrast and localization accuracy."* |
| ❌ *"All defects down to 1.0 mm depth are easily detected."* | **False:** Small defects ($D \le 6\text{ mm}$) at $z \ge 0.8\text{ mm}$ fall below detection limits due to 3D diffusion blurring. | ✅ *"Detection sensitivity degrades with depth, reaching a limit of $z \approx 0.6\text{--}0.8\text{ mm}$ for smaller inclusions."* |
| ❌ *"Our algorithms achieve 100% detection rate."* | **False:** Blind benchmark detection rates range from 0.9% to 33.2% across full 4-condition parameter space. | ✅ *"Under blind automated Otsu thresholding without prior defect knowledge, Matched Filter detected 33.2% of all defect cases."* |
| ❌ *"The thermogram simulation lasts 15 seconds."* | **False:** The simulation protocol is 10 s chirp excitation + 2 s cooling = 12 s total time (10 s exported sequence). | ✅ *"The sequence visualizes 10 seconds of active LFMT frequency sweep excitation."* |
| ❌ *"SPCT is fast enough for real-time video."* | **False:** SPCT mean runtime is 142.26 ms (~7 FPS), whereas Matched Filter (8.4 ms) and RPT (1.8 ms) achieve real-time rates (>100 FPS). | ✅ *"RPT and Matched Filtering achieve real-time throughput (>100 FPS), while SPCT requires coordinate descent iterations."* |
