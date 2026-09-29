# LFMT Slag Detection — Ground-Truth Anti-Leakage Scientific Audit

**Document Version:** 1.0 (Final Research Hardening)  
**Date:** September 2026  
**Project:** Linear Frequency-Modulated Infrared Thermography (LFMT) for Subsurface Slag Inclusion Detection in AISI 1018 Mild Steel  
**Repository:** `E:\lfmt-slag-detection`  
**Branch:** `scientific-hardening-v3`

---

## 1. Executive Summary & Objective

In non-destructive testing (NDT) and scientific machine vision benchmarks, **ground-truth leakage** occurs when prior knowledge of defect existence, location, depth, or geometry is inadvertently used by signal processing algorithms, component selectors, polarity correctors, or segmentation thresholds. Such leakage invalidates experimental claims and produces unrealistically inflated detection rates.

This audit comprehensively examines every stage of the LFMT processing pipeline to prove **zero ground-truth leakage**.

---

## 2. Mathematical Definition of Pipeline Blindness

For an acquired thermal tensor $\mathbf{T} \in \mathbb{R}^{N_t \times N_y \times N_x}$ sampled over time vector $\mathbf{t} \in \mathbb{R}^{N_t}$:
1. **Processor Isolation:**
   $$\mathbf{S}_{\text{method}}(x, y) = \mathcal{P}\big(\mathbf{T}, \mathbf{t}, \boldsymbol{\theta}_{\text{excitation}}\big)$$
   where $\boldsymbol{\theta}_{\text{excitation}} = \{f_0, f_1, T_{\text{dur}}, q_0\}$ contains only known excitation control inputs.
   $$\nabla_{\mathbf{GT}} \mathcal{P} \equiv \mathbf{0}$$
2. **Segmentation Isolation:**
   $$\hat{\mathbf{M}}(x, y) = \mathcal{S}\big(\mathbf{S}_{\text{method}}(x, y), \text{FOV}_{\text{mm}}\big)$$
   where $\mathcal{S}$ is an automated Otsu thresholding operator and morphological 8-connected component extractor.
3. **Metric Evaluation (Post-Prediction Only):**
   $$\text{IoU} = \frac{|\hat{\mathbf{M}} \cap \mathbf{M}_{\text{GT}}|}{|\hat{\mathbf{M}} \cup \mathbf{M}_{\text{GT}}|}, \quad \text{CNR} = \frac{|\mu_{\text{def}} - \mu_{\text{sound}}|}{\sqrt{\sigma_{\text{def}}^2 + \sigma_{\text{sound}}^2}}$$
   The ground-truth mask $\mathbf{M}_{\text{GT}}$ is passed strictly and exclusively to `compute_metrics.m` *after* $\hat{\mathbf{M}}$ has been output.

---

## 3. Method-by-Method Evidence & Audit

### 3.1. Raw Peak-to-Peak Contrast (`lfmt_raw_contrast.m`)
- **Inputs:** `T_surf` ($N_t \times N_y \times N_x$), `t_vec` ($N_t \times 1$).
- **Frame Selection Strategy:** Evaluates spatial standard deviation across all frames:
  $$t_{\text{peak}} = \arg\max_{t} \left( \sigma_{\text{spatial}}(T(x, y, t)) \right)$$
- **Baseline Correction:** Subtracts spatial median $\tilde{T}(t_{\text{peak}})$.
- **Audit Finding:** Zero ground-truth input. Frame selection is 100% data-driven.

### 3.2. Vectorized Matched Filter (`lfmt_matched_filter.m`)
- **Inputs:** `T_surf`, `t_vec`, $f_0, f_1, T_{\text{dur}}, q_0$.
- **Reference Waveform:** Synthesizes zero-mean AC chirp reference $r(t) = \sin(2\pi(f_0 t + \frac{1}{2}\beta t^2)) - \bar{r}$.
- **Pulse Compression:** Vectorized temporal cross-correlation:
  $$S_{\text{MF}}(x, y) = \max_{\tau} \big| (T(x,y,\cdot) * r(-\cdot))(\tau) \big|$$
- **Audit Finding:** Zero ground-truth input. Reference waveform is derived strictly from excitation control parameters.

### 3.3. SVD-PCT (`lfmt_pct.m`)
- **Inputs:** `T_surf`, `n_components`.
- **Dimensionality Reduction:** Economy Singular Value Decomposition on mean-centered matrix $\mathbf{A} = \mathbf{U} \mathbf{\Sigma} \mathbf{V}^T$.
- **Blind Component Selection:** Computes spatial skewness $\gamma_1$ and excess kurtosis $\gamma_2$:
  $$\text{Score}(i) = |\gamma_1(V_i)| \cdot \max(0.1, |\gamma_2(V_i)|)$$
  Selects $i^* = \arg\max_i \text{Score}(i)$.
- **Blind Polarity Correction:** If $\gamma_1(V_i) < 0$, inverts loading vector $V_i \gets -V_i$ to align defect anomaly with positive peak.
- **Audit Finding:** Zero ground-truth input. Component selection and sign orientation are 100% blind higher-order statistical metrics.

### 3.4. Sparse PCT (`lfmt_spct.m`)
- **Inputs:** `T_surf`, `n_components`, $\alpha_{\text{L1}}$, `max_iter`.
- **Optimization:** Coordinate-descent proximal sparse PCA with $L_1$-regularization on spatial loadings.
- **Blind Component Selection:** Anomaly score combines spatial sparsity ratio and peak-to-background ratio:
  $$\text{Score}(i) = (1 - \rho_{\text{dense}}(i)) \cdot |\gamma_1(v_i)| \cdot \frac{\max(v_i)}{\sigma(v_i)}$$
- **Audit Finding:** Zero ground-truth input.

### 3.5. Random Projection Technique (`lfmt_rpt.m`)
- **Inputs:** `T_surf`, `n_components`, `seed`.
- **Projection:** Gaussian random matrix $\boldsymbol{\Phi} \sim \mathcal{N}(0, 1/k)$ satisfying the Johnson-Lindenstrauss lemma.
- **Blind Selection:** Maximum dynamic range $\text{Score}(i) = |\gamma_1(Y_i)| \cdot (\max(Y_i) - \min(Y_i))$.
- **Audit Finding:** Zero ground-truth input.

### 3.6. Defect Segmentation (`segment_defect.m`)
- **Inputs:** `score_map`, `fov_mm`, `min_area_px`.
- **Pipeline:** Min-max normalization $\to$ Otsu thresholding $\to$ Morphological opening/closing $\to$ 8-connected component labeling $\to$ Candidate extraction and ranking by confidence $\mu_{\text{in}} - \mu_{\text{out}}$.
- **Audit Finding:** No hard-coded spatial coordinates, bounding boxes, or ground-truth defect regions are accessed.

---

## 4. Codebase String Search Audit

Automated grep search across `matlab/processing/` and `matlab/detection/` for forbidden terms:

| Search Term | Occurrences in `processing/` | Occurrences in `detection/` | Result |
|---|---|---|---|
| `ground_truth` | 0 (Only docstring disclaimer) | 0 (Only docstring disclaimer) | **PASS** |
| `gt_mask` | 0 | 0 | **PASS** |
| `defect_center` | 0 | 0 | **PASS** |
| `true_` | 0 | 0 | **PASS** |
| `radius_m` | 0 | 0 | **PASS** |
| `depth_mm` | 0 | 0 | **PASS** |

---

## 5. Conclusion

The LFMT thermography software architecture enforces strict mathematical and functional blindness. All 5 detection methods operate autonomously on raw thermal data, proving zero ground-truth leakage and ensuring complete scientific integrity for final-year project defense and publication.
