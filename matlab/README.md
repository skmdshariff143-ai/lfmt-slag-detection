# LFMT Slag Inclusion Detection: MATLAB Scientific Computing Suite

This directory contains the production-grade, research-verified MATLAB implementation for **Linear Frequency-Modulated Infrared Thermography (LFMT)** applied to subsurface slag inclusion detection in AISI 1018 mild steel weldments.

---

## 1. Live Interactive MATLAB Application (LFMT Live Lab)

You can launch and interact with the **LFMT Live Thermography Lab** via three easy options:

### Option 1: Double-Click the Windows Launcher
Double-click the launcher script in the repository root:
```cmd
E:\lfmt-slag-detection\Start_LFMT_LiveLab.bat
```
*(or double-click the **LFMT Live Thermography Lab** shortcut on your Windows Desktop).*

### Option 2: Launch Directly from MATLAB Desktop
Open MATLAB and execute:
```matlab
cd('E:\lfmt-slag-detection\matlab')
LFMTLiveLab;
```

### Option 3: Run the Flagship Visual Demo
```matlab
cd('E:\lfmt-slag-detection\matlab')
run_demo;
```

---

## 2. Interactive GUI Architecture & 6 Research Views

The **LFMT Live Thermography Lab** (`LFMTLiveLab.m`) provides an end-to-end interactive research environment structured across 6 dedicated views:

| View Tab | Scientific Purpose & Capabilities |
| :--- | :--- |
| **`🔬 LIVE INSPECTION`** | Dual-column interactive dashboard featuring the real-time front-surface thermal field $T(x,y,t)$, interactive point-and-click pixel curve inspector $T_{\text{pixel}}(t)$, 5 simultaneous blind score maps, defect boundary contours, predicted centroids, and quantitative metrics summary. |
| **`🔄 SIMULATION CONNECTION`** | Complete connected pipeline flow visualization tracking data structures through 8 stages with dynamic live status lamps: *(1) Inputs & Spec $\to$ (2) Chirp Synthesis $\to$ (3) 3-D Hex8 FEM Solver $\to$ (4) Decoupled Virtual IR Camera $\to$ (5) 5 Blind Methods $\to$ (6) Defect Segmentation $\to$ (7) Metric Evaluation $\to$ (8) Full Export Package*. |
| **`📐 FEM & 3D MODEL`** | Interactive 3-D physical geometry and discretization inspector: 3D mild steel plate volume with embedded slag cylinder, 2D cross-section schematic ($X-Z$ depth plane with convection boundaries), real 3D Hex8 element wireframe, and physical property summary table ($k, \rho, C_p, \alpha, \text{DOFs}$). |
| **`🎬 THERMAL VIDEO STUDIO`** | High-resolution thermal video player with scrubbing, variable playback speed ($0.25\times \to 4.0\times$), **Lock Color Scale** (keeps color limits fixed across all frames), dynamic excitation flux $q(t)$, transient surface temperature envelope ($T_{\max}(t), T_{\text{mean}}(t), T_{\min}(t)$), dedicated pop-out window (`🖥 Large View`), and direct **MP4 Video Export** (`VideoWriter` at 25 fps). |
| **`📊 5-METHOD BENCHMARK`** | Side-by-side high-resolution comparison grid of all 5 blind signal processing score maps (Raw Contrast, Matched Filter, SVD-PCT, SPCT, RPT) with predicted bounding boxes and overlay contours, accompanied by dual-axis CNR and IoU performance ranking charts. |
| **`📋 RESULTS & AUDIT`** | Ground-truth differential thermal contrast curve $\Delta T(t) = T_{\text{defect}}(t) - T_{\text{sound}}(t)$ (strictly labeled: *AUDIT ONLY — ISOLATED FROM DETECTORS*), active experiment parameters specification table, and export package generator. |

---

### Global Inspection & Solver Controls (Left Sidebar)
- **Defect Presets**: Quick loading for *8 mm (z=0.4 mm) [Default / Easy]*, *6 mm (z=0.4 mm) [Medium]*, *8 mm (z=0.8 mm) [Deep]*, *4 mm (z=1.0 mm) [Hard / Small]*, *Healthy Control (D=0) [No Defect]*, or *Custom Values*.
- **LFMT Excitation**: Configure chirp sweep frequencies ($f_0 \to f_1\text{ Hz}$), heat flux $q_0\text{ [W/m²]}$, and duration $T_{\text{exc}} / T_{\text{obs}}$.
- **Camera & Noise**: Choose noise conditions (*Clean*, *30 dB*, *25 dB*, *20 dB*, or *Custom SNR*) with deterministic seed control.
- **Forward Solver**: Primary 3-D Trilinear Hexahedral Finite Element Method (`MATLAB_FEM`) or Secondary 3-D Finite Difference (`MATLAB_FDM`), with resolution modes (*Standard Research*, *Quick Demo*, *High-Res Physics*).
- **Export Formats**: One-click export to `.mat` binary checkpoints, summary `.csv` metrics, `.json` configuration manifests, high-res 300 DPI `.png` figures, and high-quality `.mp4` video sequences.

---

## 3. Command-Line Workflows & Test Runners

### A. Run Master Validation Suite
```matlab
cd('E:\lfmt-slag-detection\matlab')
val_results = run_validation_suite('Quick', false);
```

### B. Run Full 4,030-Evaluation Scientific Study
```matlab
cd('E:\lfmt-slag-detection\matlab')
study_results = run_full_study('Quick', false);
```

### C. Run Automated MATLAB Test Suite (34/34 Tests)
```matlab
cd('E:\lfmt-slag-detection\matlab')
test_results = run_tests();
```

---

## 2. Architecture & Directory Layout

```
matlab/
├── run_project.m                 % Master pipeline orchestrator ('demo', 'validate', 'test', 'study_full')
├── run_single_case.m              % Single case execution & visualizer
├── run_full_study.m               % Full 26 cases x 31 conditions = 806 runs x 5 methods = 4,030 evals
├── run_validation_suite.m         % Numerical & physical validation suite
├── run_demo.m                     % Flagship interactive demo
├── run_tests.m                    % Native MATLAB test suite runner
├── lfmt_check_environment.m       % Runtime toolbox and capability detector
├── lfmt_setup_paths.m             % Search path initialization utility
│
├── config/
│   ├── default_config.m           % Standard validated baseline configuration
│   ├── conference_config.m        % Frozen conference benchmark configuration
│   ├── literature_config.m        % Classical NDT literature configuration
│   └── physics_optimized_config.m % Diffusion-length optimized configuration
│
├── +lfmt/
│   ├── materials.m                % Thermophysical property database (AISI 1018, slag, air, SS304)
│   ├── excitation.m               % LFMT linear frequency chirp, instantaneous phase, diffusion length
│   ├── geometry.m                 % Parameterized 3D geometry & defect definitions
│   ├── camera.m                   % Decoupled spatial & temporal virtual IR camera sampling
│   ├── noise.m                    % Deterministic multi-seed AWGN injection (Clean, 30dB, 25dB, 20dB)
│   ├── preprocessing.m            % Mean removal and linear temporal detrending
│   ├── cache.m                    % SHA-256 disk caching & fast checkpointing
│   └── utils.m                    % Mathematical & visualization utilities
│
├── simulation/
│   ├── lfmt_simulate_fem.m        % Genuine 3-D Trilinear Hexahedral Finite Element Method (Hex8) Solver
│   ├── lfmt_simulate_fdm.m        % 3-D Conservative Finite Difference Solver (MATLAB_FDM)
│   └── compare_fem_fdm.m          % Quantitative cross-validation between FEM and FDM
│
├── processing/
│   ├── lfmt_raw_contrast.m        % Blind Raw Thermal Contrast
│   ├── lfmt_matched_filter.m      % Blind Matched Filter / Pulse Compression (Vectorized conv2)
│   ├── lfmt_pct.m                 % Blind SVD-PCT with excess kurtosis selection
│   ├── lfmt_spct.m                % Blind L1-Sparse PCA with peak-to-background anomaly selection
│   └── lfmt_rpt.m                 % Blind Random Projection with dynamic range selection
│
├── detection/
│   ├── normalize_score_map.m      % Robust [0, 1] normalization
│   ├── compute_otsu_threshold.m   % Pure MATLAB Otsu global binarization
│   └── segment_defect.m           % Morphological filtering & 8-connectivity candidate extraction
│
├── evaluation/
│   ├── compute_metrics.m          % IoU, Dice, Precision, Recall, Localization Error, Diameter Error, CNR
│   ├── compute_roc_pr_curves.m    % Pixel-level ROC AUC and PR AP curves
│   ├── detection_success.m        % 3-tier formal detection success classifier
│   ├── maximum_detectable_depth.m % z_max calculation (>= 80% success)
│   └── aggregate_results.m        % Summary table generation by method, depth, diameter, and noise
│
├── validation/
│   ├── validate_mesh.m            % Spatial mesh independence (Coarse, Medium, Fine)
│   ├── validate_timestep.m        % Temporal time-step independence (dt, dt/2, dt/4)
│   ├── validate_physics.m         % Zero-flux, scaling linearity, material contrast, depth attenuation
│   ├── validate_sensitivity.m     % Parameter sensitivity (q0, k_slag, h_conv, Cp_slag)
│   └── validate_python_parity.m   % Cross-language Python vs MATLAB parity audit
│
├── visualization/
│   ├── plot_thermograms.m         % 4-snapshot spatial evolution & transient curves
│   ├── plot_method_comparison.m   % Side-by-side 5-method comparison with GT overlay
│   ├── plot_depth_results.m       % Performance vs Defect Depth curves
│   ├── plot_diameter_results.m    % Performance vs Defect Diameter curves
│   ├── plot_noise_results.m       % Noise robustness curves across AWGN levels
│   └── plot_validation_results.m  % Numerical verification & sensitivity bar chart
│
├── tests/
│   ├── TestLFMTCameraAndNoise.m
│   ├── TestLFMTDetectionAndMetrics.m
│   ├── TestLFMTExcitation.m
│   ├── TestLFMTFEMSimulation.m
│   ├── TestLFMTMaterials.m
│   ├── TestLFMTProcessingBlindness.m
│   └── TestLFMTValidationRoutines.m
│
└── results/
    ├── cache/                     % SHA-256 simulation checkpoints & .mat files
    ├── tables/                    % Summary CSV tables
    ├── figures/                   % 300+ DPI publication figures
    ├── validation/                % Validation CSV reports
    └── manifests/                 % JSON study provenance manifests
```

---

## 3. Mathematical & Numerical Principles

### A. 3-D Hexahedral Finite Element Formulation (Hex8)
The weak form of the transient heat conduction equation is discretized using 8-node trilinear hexahedral elements:
$$(\mathbf{M}/\Delta t + \mathbf{K} + \mathbf{M}_{\text{conv}}) \mathbf{T}^{n+1} = (\mathbf{M}/\Delta t) \mathbf{T}^n + q(t^{n+1}) \mathbf{f}_{\text{front}} + \mathbf{f}_{\text{amb}}$$
- The global system matrix $\mathbf{A} = \mathbf{M}/\Delta t + \mathbf{K} + \mathbf{M}_{\text{conv}}$ is symmetric positive definite and pre-factorized via sparse Cholesky decomposition (`decomposition(A, 'chol', 'lower')`), yielding fast implicit time stepping.

### B. Strict Anti-Leakage Protocol
Ground truth defect coordinates and masks are strictly isolated from signal processing, component selection, polarity alignment, thresholding, and segmentation.
- **Raw Contrast**: Blind frame selection via maximum spatial variance $\text{argmax}_t (\sigma_{\text{spatial}}(T(t)))$.
- **Matched Filter**: Vectorized cross-correlation against zero-mean AC chirp reference.
- **PCT**: SVD on mean-centered temporal data ($K=6$); blind EOF selection via spatial excess kurtosis $\kappa = |\mu_4/\sigma^4 - 3|$ and skewness polarity alignment.
- **SPCT**: $L_1$-regularized Sparse PCA ($\alpha = 0.05$); blind component selection via peak-to-background anomaly ratio and spatial sparsity weighting.
- **RPT**: Gaussian random projection $\mathbf{\Phi} \sim \mathcal{N}(0, 1/K)$; blind component selection via dynamic range $\text{ptp}(S)$.
