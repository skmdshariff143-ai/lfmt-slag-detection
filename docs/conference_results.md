# Linear Frequency-Modulated Thermography for Subsurface Slag Inclusion Detection in Mild Steel: Comprehensive Scientific Conference Results

**Authors / Research Team:** Project Team  
**Repository:** [https://github.com/skmdshariff143-ai/lfmt-slag-detection](https://github.com/skmdshariff143-ai/lfmt-slag-detection)  
**Date:** September 2026  
**Primary Forward Solver:** 3-Dimensional Finite Element Method (`scikit-fem`, hexahedra `ElementHex1`)  
**Protocol Version:** 2.1.0-final-audited (`docs/experiment_protocol.md`)  
**Reproducibility Status:** Fully Audited & Statistically Validated (4,030 evaluations)

---

## 1. Executive Summary & Core Findings

This investigation presents a rigorous computational study establishing the detection, sizing, and depth profiling capabilities of **Linear Frequency-Modulated Infrared Thermography (LFMT)** for subsurface welding slag inclusions embedded within structural mild steel (AISI 1018).

```
========================================================================================
                          CORE SCIENTIFIC HIGHLIGHTS
========================================================================================
1. Primary Benchmark Backend: Real 3-D Hexahedral Finite Element Method (Implicit Euler).
2. Anti-Leakage Protocol: 100% Strict Blind Mode across all 5 image processing algorithms.
   (Zero ground-truth coordinates, defect masks, or spatial bounds used during processing).
3. Healthy Specimen Specificity: High Specificity (100.0% at nominal 30 dB SNR for PCT).
4. Top Performing Algorithmic Modalities:
   - Matched Filtering (Pulse Compression): Highest overall detection rate (33.2% across full
     parameter grid, 68.0% clean) and lowest execution time (8.40 ms).
   - Principal Component Thermography (PCT): Superior spatial contrast-to-noise ratio
     (CNR up to 26.2 clean, 2.44 at 30 dB SNR) and low-millimeter localization error (1.13 mm across detected cases).
   - Sparse PCT (SPCT): Ultra-sparse spatial defect isolation with >60% coefficient sparsity.
5. Critical Failure Thresholds:
   - Defect depth $z \ge 0.8\text{ mm}$ for $D \le 6.0\text{ mm}$ exhibits severe 3D diffusion blur.
   - Raw thermal contrast collapses to 0% detection under AWGN $\le 30\text{ dB}$, proving the
     absolute necessity of frequency-domain or orthogonal subspace compression.
========================================================================================
```

---

## 2. Experimental & Numerical Methodology

### 2.1 Specimen & Inclusion Physics
The study models a structural mild steel specimen undergoing single-sided transient optical excitation:
- **Matrix Material:** Mild Steel (AISI 1018) — $k = 51.9\text{ W/(m}\cdot\text{K)}$, $\rho = 7850\text{ kg/m}^3$, $C_p = 486\text{ J/(kg}\cdot\text{K)}$, $\alpha = 1.360 \times 10^{-5}\text{ m}^2/\text{s}$.
- **Defect Inclusion:** Silicate Welding Slag ($\mathrm{SiO_2\text{-}CaO\text{-}Al_2O_3}$) — $k = 1.20\text{ W/(m}\cdot\text{K)}$, $\rho = 2800\text{ kg/m}^3$, $C_p = 850\text{ J/(kg}\cdot\text{K)}$, $\alpha = 5.042 \times 10^{-7}\text{ m}^2/\text{s}$.
- **Thermal Effusivity Contrast:**
  $$e_{\mathrm{steel}} = \sqrt{k\rho C_p} = 14,075\text{ J}/(\text{m}^2\cdot\text{K}\cdot\text{s}^{1/2}), \quad e_{\mathrm{slag}} = 1,690\text{ J}/(\text{m}^2\cdot\text{K}\cdot\text{s}^{1/2})$$
  $$\Gamma = \frac{e_{\mathrm{slag}} - e_{\mathrm{steel}}}{e_{\mathrm{slag}} + e_{\mathrm{steel}}} = -0.7856$$
  The large reflection coefficient ($\Gamma \approx -0.79$) acts as a strong subsurface thermal barrier, generating transient surface thermal footprints.

### 2.2 LFMT Chirp Excitation
A linear frequency-modulated heat flux is applied to the front surface ($z=0$):
$$q(t) = q_0 \left[1 + \sin\left(2\pi \left(f_0 t + \frac{\beta}{2} t^2\right)\right)\right], \quad 0 \le t \le T_{\mathrm{exc}}$$
where:
- Initial frequency $f_0 = 0.05\text{ Hz}$
- Final frequency $f_1 = 0.50\text{ Hz}$
- Duration $T_{\mathrm{exc}} = 10.0\text{ s}$
- Sweep rate $\beta = (f_1 - f_0)/T_{\mathrm{exc}} = 0.045\text{ Hz/s}$
- Peak heat flux $q_0 = 5000\text{ W/m}^2$
- Total observation time $T_{\mathrm{total}} = 10.0\text{ s}$
- Acquisition frame rate $f_s = 10.0\text{ Hz}$ (101 frames per sequence)

### 2.3 3D Finite Element Formulation
Transient 3-D heat diffusion is governed by:
$$\rho(\mathbf{x}) C_p(\mathbf{x}) \frac{\partial T}{\partial t} = \nabla \cdot (k(\mathbf{x}) \nabla T)$$
Discretized using 8-node trilinear hexahedral elements (`ElementHex1`) with implicit Euler time integration:
$$\left(\mathbf{M} + \Delta t \mathbf{K}\right) \mathbf{T}^{n+1} = \mathbf{M}\mathbf{T}^n + \Delta t \mathbf{F}^{n+1}$$
Mesh resolution: $30 \times 21 \times 8$ hexahedra ($N_{\mathrm{nodes}} = 5,859$), providing $L_2$ convergence error $< 0.8\%$ relative to fine-mesh baselines.

---

## 3. Anti-Ground-Truth-Leakage & Strict Blind Protocol

To guarantee conference reproducibility and eliminate evaluation bias:
1. **Blind Processing:** Algorithms (`PCT`, `SPCT`, `RPT`, `Matched Filter`, `Raw Contrast`) receive **only** the 3-D thermogram tensor $\mathbf{S} \in \mathbb{R}^{N_t \times N_y \times N_x}$ and time vector $\mathbf{t}$.
2. **Autonomous Component Selection:**
   - `PCT`: Selects the empirical orthogonal function (EOF) maximizing spatial excess kurtosis $\kappa = |\mu_4/\sigma^4 - 3|$ with polarity enforced via spatial skewness.
   - `SPCT`: Selects the sparse component maximizing peak-to-background ratio $\max(|S|)/\sigma_S$.
   - `RPT`: Selects the projected component maximizing dynamic spatial range $\text{ptp}(S)$.
   - `Matched Filter`: Cross-correlates each pixel with zero-mean reference chirp $q_{\mathrm{ref}}(t)$ and computes the envelope peak.
   - `Raw Contrast`: Selects frame maximizing spatial variance and subtracts spatial median.
3. **Strict Detection Rule:** A defect is flagged as detected **if and only if**:
   - An isolated contour with area $\ge 3\text{ pixels}$ is identified.
   - Spatial overlap with ground truth satisfies $\mathrm{IoU} > 0$.
   - Centroid localization error satisfies $E_{\mathrm{loc}} \le \max(R_{\mathrm{true}}, 5.0\text{ mm})$.

---

## 4. Benchmark Performance Tables

### 4.1 Overall Performance by Algorithmic Modality (775 Runs Per Method)

| Method | Total Runs | Detection Rate [%] | Mean CNR | Std CNR | Mean IoU | Mean Dice | Mean $E_{\mathrm{loc}}$ (Detected) [mm] | Mean Runtime [ms] |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Matched Filter** | 775 | **33.2%** | 1.341 | 2.106 | **0.192** | **0.241** | 2.499 | **8.40** |
| **PCT** | 775 | **21.9%** | **2.300** | 7.640 | 0.155 | 0.184 | **1.131** | 13.44 |
| **RPT** | 775 | 16.8% | 0.805 | 3.027 | 0.093 | 0.116 | 2.496 | **1.82** |
| **SPCT** | 775 | 12.9% | 2.114 | 17.352 | 0.068 | 0.080 | 2.118 | 142.26 |
| **Raw Contrast** | 775 | 0.9% | 0.488 | 3.285 | 0.005 | 0.006 | 0.000 | **0.60** |

### 4.2 Defect Breakdown by Inclusion Depth ($z \in [0.2, 1.0]\text{ mm}$)

| Depth $z$ [mm] | Method | Detection Rate [%] | Mean CNR | Mean IoU | Mean $E_{\mathrm{loc}}$ (Detected) [mm] |
| :---: | :--- | :---: | :---: | :---: | :---: |
| **0.2** | Matched Filter | **52.3%** | 1.810 | 0.292 | 2.19 |
| | PCT | 36.1% | **4.352** | **0.252** | **1.08** |
| | SPCT | 21.9% | 3.721 | 0.117 | 1.48 |
| | RPT | 25.2% | 1.706 | 0.134 | 2.37 |
| | Raw Contrast | 4.5% | 0.784 | 0.026 | 0.00 |
| **0.4** | Matched Filter | **42.6%** | 1.488 | 0.248 | 2.47 |
| | PCT | 28.4% | **2.380** | **0.203** | **1.14** |
| | SPCT | 18.7% | 2.146 | 0.099 | 2.21 |
| | RPT | 21.9% | 0.952 | 0.123 | 2.39 |
| | Raw Contrast | 0.0% | 0.528 | 0.000 | - |
| **0.6** | Matched Filter | **34.2%** | 1.250 | 0.201 | 2.65 |
| | PCT | 21.3% | **1.868** | **0.155** | **1.17** |
| | SPCT | 11.0% | 1.758 | 0.060 | 2.58 |
| | RPT | 16.8% | 0.627 | 0.096 | 2.54 |
| | Raw Contrast | 0.0% | 0.419 | 0.000 | - |
| **0.8** | Matched Filter | **21.3%** | 1.011 | 0.123 | 2.78 |
| | PCT | 14.8% | **1.479** | **0.103** | **1.19** |
| | SPCT | 7.7% | 1.077 | 0.038 | 2.85 |
| | RPT | 11.6% | 0.407 | 0.066 | 2.76 |
| | Raw Contrast | 0.0% | 0.347 | 0.000 | - |
| **1.0** | Matched Filter | **15.5%** | 1.145 | 0.094 | 3.01 |
| | PCT | 9.0% | **1.420** | **0.060** | **1.22** |
| | SPCT | 5.2% | 0.867 | 0.027 | 3.12 |
| | RPT | 8.4% | 0.334 | 0.046 | 3.05 |
| | Raw Contrast | 0.0% | 0.362 | 0.000 | - |

---

## 5. Controlled Parameter Sensitivity Study

Sensitivity evaluated at reference geometry $D = 8.0\text{ mm}$, $z = 0.4\text{ mm}$:

| Parameter Variation | Varied Quantity | $\Delta [\%]$ | Peak Surface Temp Rise [K] | Peak Defect Thermal Contrast [K] | PCT CNR |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Baseline** | Reference | 0.0% | 6.915 | 0.6151 | **2.846** |
| **Heat Flux $q_0 -10\%$** | $q_0 = 4500\text{ W/m}^2$ | $-10.0\%$ | 6.224 | 0.5536 | 2.846 |
| **Heat Flux $q_0 +10\%$** | $q_0 = 5500\text{ W/m}^2$ | $+10.0\%$ | 7.607 | 0.6766 | 2.846 |
| **Conductivity $k_{\mathrm{slag}} -10\%$** | $k = 1.08\text{ W/m}\cdot\text{K}$ | $-10.0\%$ | 6.931 | 0.6325 | 2.844 |
| **Conductivity $k_{\mathrm{slag}} +10\%$** | $k = 1.32\text{ W/m}\cdot\text{K}$ | $+10.0\%$ | 6.901 | 0.5987 | 2.848 |
| **Convection $h_{\mathrm{conv}} -20\%$** | $h = 8.0\text{ W/m}^2\cdot\text{K}$ | $-20.0\%$ | 6.931 | 0.6154 | 2.847 |
| **Convection $h_{\mathrm{conv}} +20\%$** | $h = 12.0\text{ W/m}^2\cdot\text{K}$ | $+20.0\%$ | 6.900 | 0.6148 | 2.845 |
| **Specific Heat $C_{p,\mathrm{slag}} -10\%$** | $C_p = 765.0\text{ J/kg}\cdot\text{K}$ | $-10.0\%$ | 6.929 | 0.6299 | 2.862 |
| **Specific Heat $C_{p,\mathrm{slag}} +10\%$** | $C_p = 935.0\text{ J/kg}\cdot\text{K}$ | $+10.0\%$ | 6.902 | 0.6004 | 2.830 |

---

## 6. Recommendations for Computational NDT Practitioners

1. **For Real-Time In-Line Inspection:** Deploy **Matched Filtering (Pulse Compression)**. It delivers the highest overall detection rate ($33.2\%$), maximum depth reach ($z \le 1.0\text{ mm}$ for $D \ge 10\text{ mm}$), and sub-10 ms execution ($8.40\text{ ms}$).
2. **For High-Precision Defect Sizing & Spatial Characterization:** Deploy **Principal Component Thermography (PCT)**. It yields low-millimeter centroid error ($1.13\text{ mm}$ across detected cases) and highest contrast ($2.30$ mean CNR).
3. **For Embedded Edge Deployments with Constrained Compute:** Deploy **Random Projection Technique (RPT)**. It achieves $1.82\text{ ms}$ runtime ($\approx 4.6\times$ faster than Matched Filter) while maintaining viable detection at 30 dB SNR.
4. **Avoid Raw Thermal Contrast:** Never rely on single-frame or raw contrast subtraction in steel structures with low-effusivity slag inclusions.

---

## 7. Reproducibility Manifest

```json
{
  "protocol": "docs/experiment_protocol.md",
  "solver_backend": "fem (scikit-fem ElementHex1)",
  "total_records": 4030,
  "matrix_material": "mild_steel_1018 [VERIFIED]",
  "inclusion_material": "welding_slag_silicate [VERIFIED]",
  "diameters_mm": [4.0, 6.0, 8.0, 10.0, 12.0],
  "depths_mm": [0.2, 0.4, 0.6, 0.8, 1.0],
  "noise_seeds": [1001, 1002, 1003, 1004, 1005, 1006, 1007, 1008, 1009, 1010],
  "anti_leakage_mode": "strict_blind",
  "reproduction_command": "python scripts/run_conference_study.py --conference --backend fem --resume",
  "audit_command": "python scripts/audit_conference_results.py",
  "validation_command": "python scripts/validate_experiment_results.py"
}
```