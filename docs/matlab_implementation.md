# MATLAB Implementation Architecture & Mathematical Formulation

## 1. Executive Summary

This document describes the pure MATLAB implementation of the **Linear Frequency-Modulated Infrared Thermography (LFMT / FMTWI)** forward numerical simulation, virtual infrared acquisition, blind thermographic signal processing, and defect detection suite for subsurface silicate slag inclusion evaluation in mild steel weldments.

The implementation is structured under the `matlab/` directory using modern MATLAB package conventions (`+lfmt/`) and standard engineering modularity. It provides:
- A genuine **3-D Trilinear Hexahedral Finite Element Method (`Hex8`)** forward solver.
- A secondary **3-D Conservative Finite Difference Method (`FDM`)** reference solver.
- Five **strictly blind thermographic signal processing algorithms** (Raw Contrast, Vectorized Matched Filter / Pulse Compression, SVD-PCT, Coordinate-Descent Sparse PCA / SPCT, Gaussian Random Projection / RPT).
- A **blind morphological detection and segmentation pipeline**.
- Quantitative performance evaluation with **ground truth isolation**.

---

## 2. Mathematical & Physical Formulation

### 2.1 3-D Transient Heat Conduction Equation
The 3-D transient temperature field $T(x, y, z, t)$ in Cartesian coordinates $(x,y,z) \in \Omega = [0, L_x] \times [0, L_y] \times [0, L_z]$ for $t \in [0, t_{\text{sim}}]$ is governed by:

$$\rho(x,y,z) C_p(x,y,z) \frac{\partial T}{\partial t} = \nabla \cdot \left( k(x,y,z) \nabla T \right)$$

where:
- $k(x,y,z)$ is the spatial thermal conductivity $[\text{W}/(\text{m}\cdot\text{K})]$.
- $\rho(x,y,z)$ is the spatial mass density $[\text{kg}/\text{m}^3]$.
- $C_p(x,y,z)$ is the spatial specific heat capacity $[\text{J}/(\text{kg}\cdot\text{K})]$.

### 2.2 Boundary and Initial Conditions

1. **Front Surface ($z = 0$):**
   $$-k \frac{\partial T}{\partial z}\Big|_{z=0} = q_{\text{LFMT}}(t) - h \left( T(x,y,0,t) - T_{\text{amb}} \right)$$

2. **Rear Surface ($z = L_z$):**
   $$-k \frac{\partial T}{\partial z}\Big|_{z=L_z} = h \left( T(x,y,L_z,t) - T_{\text{amb}} \right)$$

3. **Lateral Surfaces ($x = 0, x = L_x, y = 0, y = L_y$):**
   $$-k \nabla T \cdot \hat{\mathbf{n}} = h \left( T - T_{\text{amb}} \right)$$

4. **Initial Thermal State ($t = 0$):**
   $$T(x,y,z,0) = T_{\text{amb}} = 293.15\text{ K}$$

### 2.3 LFMT Linear Frequency-Modulated Excitation
The optical heat flux is linearly chirped from $f_0 = 0.05\text{ Hz}$ to $f_1 = 0.50\text{ Hz}$ over duration $T_{\text{exc}} = 10.0\text{ s}$:

$$q_{\text{LFMT}}(t) = \begin{cases} q_0 \cdot \frac{1}{2} \left[ 1 + \sin\left(2\pi \left( f_0 t + \frac{f_1 - f_0}{2 T_{\text{exc}}} t^2 \right) - \frac{\pi}{2} \right) \right] & \text{for } 0 \le t \le T_{\text{exc}} \\ 0 & \text{for } t > T_{\text{exc}} \end{cases}$$

The zero-mean AC reference waveform used for matched filtering is:
$$q_{\text{ref}}(t) = \sin\left(2\pi \left( f_0 t + \frac{f_1 - f_0}{2 T_{\text{exc}}} t^2 \right) - \frac{\pi}{2}\right)$$

---

## 3. Finite Element Method (Hex8) Formulation

### 3.1 Weak Form
Multiplying the governing PDE by test functions $v(x,y,z) \in H^1(\Omega)$ and integrating by parts yields:

$$\int_{\Omega} \rho C_p \frac{\partial T}{\partial t} v \, d\Omega + \int_{\Omega} k \nabla T \cdot \nabla v \, d\Omega + \int_{\partial \Omega} h T v \, d\Gamma = \int_{\Gamma_{\text{front}}} q_{\text{LFMT}}(t) v \, d\Gamma + \int_{\partial \Omega} h T_{\text{amb}} v \, d\Gamma$$

### 3.2 Discrete System & Kronecker Element Matrices
The domain is discretized into structured 8-node trilinear hexahedral elements (`Hex8`). For an element $e$ of dimensions $\Delta x \times \Delta y \times \Delta z$:

- **1D 2-node elemental mass and stiffness stencils:**
  $$m_{1\text{D}} = \frac{\Delta s}{6} \begin{bmatrix} 2 & 1 \\ 1 & 2 \end{bmatrix}, \quad k_{1\text{D}} = \frac{1}{\Delta s} \begin{bmatrix} 1 & -1 \\ -1 & 1 \end{bmatrix}$$

- **3D 8-node Element Matrices via Tensor Products:**
  $$\mathbf{M}^e = \rho_e C_{p,e} \left( m_x \otimes m_y \otimes m_z \right)$$
  $$\mathbf{K}^e = k_e \left( k_x \otimes m_y \otimes m_z + m_x \otimes k_y \otimes m_z + m_x \otimes m_y \otimes k_z \right)$$

- **Surface Convection Matrices:**
  $$\mathbf{H}^e_{\text{face}} = h \left( m_u \otimes m_v \right)$$

### 3.3 Implicit Euler Time Integration & Pre-Factorization
Applying backward (implicit) Euler discretization:

$$\left( \frac{\mathbf{M}}{\Delta t} + \mathbf{K} + \mathbf{H} \right) \mathbf{T}^{n+1} = \frac{\mathbf{M}}{\Delta t} \mathbf{T}^n + \mathbf{F}_{\text{front}}(t^{n+1}) + \mathbf{F}_{\text{conv}}$$

Let $\mathbf{A} = \frac{\mathbf{M}}{\Delta t} + \mathbf{K} + \mathbf{H}$. Because $\mathbf{A}$ is constant over time, symmetric positive-definite, and sparse:
1. $\mathbf{A}$ is assembled once in sparse format (`sparse`).
2. Symmetrization is strictly enforced: $\mathbf{A} = \frac{1}{2}(\mathbf{A} + \mathbf{A}^T)$.
3. The lower Cholesky decomposition is computed once prior to the time-stepping loop:
   $$\mathbf{L} = \text{decomposition}(\mathbf{A}, \text{'chol'}, \text{'lower'})$$
4. At each time step $n$, $\mathbf{T}^{n+1}$ is computed via fast triangular back-substitution:
   $$\mathbf{T}^{n+1} = \mathbf{L} \backslash \mathbf{b}^{n+1}$$

---

## 4. Thermographic Signal Processing Algorithms

All five processing methods operate **strictly without access to defect geometry, spatial location, depth, or presence**.

### 4.1 Raw Contrast
- Selects the single 2-D thermogram frame that maximizes spatial variance across the plate surface:
  $$t^* = \arg\max_t \text{Var}_{(x,y)} \left( T(x,y,t) \right)$$
- Subtracts the spatial median and computes absolute contrast:
  $$S(x,y) = |T(x,y,t^*) - \text{median}(T(x,y,t^*))|$$

### 4.2 Matched Filter / Pulse Compression
- Cross-correlates each pixel's AC temperature response $\widetilde{T}(x,y,t) = T(x,y,t) - \bar{T}(x,y)$ with the zero-mean reference excitation chirp $q_{\text{ref}}(t)$:
  $$R_{xy}(\tau) = \int_0^{t_{\text{sim}}} \widetilde{T}(x,y,t) q_{\text{ref}}(t - \tau) \, dt$$
- Implemented as a high-speed vectorized 2-D convolution across all pixels:
  $$S(x,y) = \max_{\tau} |R_{xy}(\tau)|$$

### 4.3 Principal Component Thermography (SVD-PCT)
- Unrolls the mean-centered 3-D thermogram sequence into a matrix $\mathbf{X} \in \mathbb{R}^{N_p \times N_t}$ ($N_p = N_x \times N_y = 4096$).
- Computes Singular Value Decomposition: $\mathbf{X} = \mathbf{U} \mathbf{\Sigma} \mathbf{V}^T$.
- Evaluates the first $K=6$ spatial EOFs ($\mathbf{U}_k$).
- **Blind Component Selection:** Computes spatial anomaly score $A_k = |\text{skewness}(\mathbf{U}_k)| \cdot |\text{kurtosis}(\mathbf{U}_k)|$. The component with the highest $A_k$ is selected.
- **Blind Polarity Alignment:** If $\text{skewness}(\mathbf{U}_{k^*}) < 0$, the EOF is inverted ($\mathbf{U}_{k^*} \leftarrow -\mathbf{U}_{k^*}$) so that the anomalous region forms a positive peak.

### 4.4 Sparse Principal Component Thermography (SPCT)
- Implements $L_1$-penalized coordinate descent sparse PCA ($\alpha=0.05, K=6$) to enforce spatial compactness of defects.
- Selects the component maximizing spatial sparsity weighting and peak-to-background ratio.
- Inverts polarity if skewness is negative.

### 4.5 Random Projection Thermography (RPT)
- Generates a Gaussian random projection matrix $\mathbf{\Phi} \in \mathbb{R}^{N_t \times K}$ with $\Phi_{ij} \sim \mathcal{N}(0, 1/K)$.
- Projects data: $\mathbf{Y} = \mathbf{X} \mathbf{\Phi}$.
- Selects the projection maximizing dynamic range $\text{ptp}(\mathbf{Y}_k)$ and aligns polarity based on spatial skewness.

---

## 5. Blind Detection & Segmentation Pipeline

1. **Normalization:** The selected 2-D score map is min-max scaled to $[0, 1]$.
2. **Binarization:** An adaptive threshold $\tau_{\text{Otsu}}$ is computed via Otsu's method on the normalized map.
3. **Morphological Filtering:** A $3 \times 3$ structuring element performs morphological opening (to eliminate isolated noise pixels) followed by morphological closing (to bridge intra-defect gaps).
4. **Candidate Extraction:** 8-connected components are labeled (`bwlabel`).
5. **Defect Confirmation:**
   - For healthy plates ($D=0\text{ mm}$), any candidate must pass an area threshold ($A \ge 3\text{ px}$) and prominence check. If no significant cluster exists, detection correctly returns `detected = false`.
   - For defective plates, the largest connected component is extracted, and its centroid $(\bar{x}, \bar{y})$ and equivalent diameter $D_{\text{eq}} = 2\sqrt{A/\pi} \cdot \Delta x_{\text{cam}}$ are computed.

---

## 6. Directory Structure & File Map

```
matlab/
├── +lfmt/                      # Core LFMT package
│   ├── cache.m                 # SHA-256 deterministic caching
│   ├── camera.m                # Virtual IR camera & gridded interpolation
│   ├── excitation.m            # LFMT linear chirp waveform & diffusion lengths
│   ├── geometry.m              # 3D plate/inclusion geometric parameterization
│   ├── materials.m             # Thermophysical material property database
│   ├── noise.m                 # Multi-seed deterministic AWGN generator
│   ├── preprocessing.m         # Mean-centering and detrending utilities
│   └── utils.m                 # Formatting and math utilities
├── config/                     # Configuration presets
│   ├── default_config.m        # Standard research baseline
│   ├── conference_config.m     # Fast conference demonstration preset
│   ├── literature_config.m     # Literature validation preset
│   └── physics_optimized_config.m # High-fidelity spatial mesh preset
├── simulation/                 # Forward numerical solvers
│   ├── lfmt_simulate_fem.m     # 3-D Hex8 Trilinear FEM solver (Primary)
│   ├── lfmt_simulate_fdm.m     # 3-D Finite Difference Method solver (Secondary)
│   └── compare_fem_fdm.m       # FEM vs FDM quantitative benchmark
├── processing/                 # Blind thermographic processing methods
│   ├── lfmt_raw_contrast.m     # Blind maximum-variance raw contrast
│   ├── lfmt_matched_filter.m   # Vectorized pulse compression cross-correlation
│   ├── lfmt_pct.m              # SVD-PCT with skewness/kurtosis component selection
│   ├── lfmt_spct.m             # Sparse PCA coordinate descent
│   └── lfmt_rpt.m              # Gaussian random projection
├── detection/                  # Defect segmentation & extraction
│   ├── compute_otsu_threshold.m# Otsu global thresholding
│   ├── normalize_score_map.m   # Dynamic range min-max scaling
│   └── segment_defect.m        # Morphological opening/closing & 8-connectivity
├── evaluation/                 # Metrics & statistical aggregators
│   ├── compute_metrics.m       # IoU, Dice, Loc Error, Diam Error, CNR, ROC, PR
│   ├── detection_success.m     # 3-criterion formal detection classifier
│   ├── maximum_detectable_depth.m # 80% detection threshold depth finder
│   └── aggregate_results.m     # Summary table compiler
├── validation/                 # Numerical validation suite
│   ├── validate_mesh.m         # Spatial mesh convergence (Coarse, Med, Fine)
│   ├── validate_timestep.m     # Temporal convergence (dt = 0.08, 0.04, 0.02 s)
│   ├── validate_physics.m      # 5/5 physical sanity checks
│   ├── validate_sensitivity.m  # Parameter perturbation sensitivity study
│   └── validate_python_parity.m# Python-MATLAB cross-language parity
├── visualization/              # Publication figure generators (300 DPI)
│   ├── plot_thermograms.m      # Fig 4: Transient surface evolution
│   ├── plot_method_comparison.m# Fig 10: 5-method visual comparison
│   ├── plot_depth_results.m    # Fig 11: Performance vs depth
│   ├── plot_diameter_results.m # Fig 12: Performance vs diameter
│   ├── plot_noise_results.m    # Fig 16: Robustness across SNR
│   └── plot_validation_results.m # Fig 18: Mesh/timestep/parity validation summary
├── tests/                      # MATLAB Unit Test Suite (28 / 28 passing)
├── run_tests.m                 # Test runner script
├── run_demo.m                  # Fast interactive demonstration
├── run_single_case.m           # Single parameterized case runner
├── run_validation_suite.m      # Comprehensive verification runner
├── run_full_study.m            # 4,030-evaluation benchmark runner
├── run_project.m               # Complete end-to-end master pipeline
├── lfmt_setup_paths.m          # Path initialization
├── lfmt_check_environment.m    # Environment & toolbox auditor
└── README.md                   # MATLAB module documentation
```
