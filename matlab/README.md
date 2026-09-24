# LFMT Slag Inclusion Detection: MATLAB Scientific Computing Suite

This directory contains the production-grade, research-verified MATLAB implementation for **Linear Frequency-Modulated Infrared Thermography (LFMT)** applied to subsurface slag inclusion detection in AISI 1018 mild steel weldments.

---

## 1. Quick Start

### A. Run Interactive Flagship Demo
```matlab
cd matlab
res = run_demo();
```

### B. Run Master Validation Suite
```matlab
cd matlab
val_results = run_validation_suite('Quick', false);
```

### C. Run Full 4,030-Evaluation Scientific Study
```matlab
cd matlab
study_results = run_full_study('Quick', false);
```

### D. Run Automated MATLAB Test Suite
```matlab
cd matlab
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
