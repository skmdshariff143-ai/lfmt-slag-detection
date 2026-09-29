# Python vs MATLAB Numerical Parity Report

## 1. Overview

This document reports the cross-language numerical parity analysis between the Python numerical reference engine and the MATLAB research implementation for Linear Frequency-Modulated Infrared Thermography.

Both implementations were subjected to identical geometric parameterizations, material thermophysical properties, excitation waveforms, boundary conditions, and spatial/temporal discretization parameters.

---

## 2. Quantitative Parity Comparison

| Metric / Characteristic | Python Reference | MATLAB Hex8 FEM | Absolute Difference | Parity Tolerance | Status |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **AISI 1018 Conductivity $k$** | $51.9\text{ W}/(\text{m}\cdot\text{K})$ | $51.9\text{ W}/(\text{m}\cdot\text{K})$ | $0.00\text{ W}/(\text{m}\cdot\text{K})$ | Exact ($0.0$) | **PASSED** |
| **Silicate Slag Conductivity $k$** | $1.20\text{ W}/(\text{m}\cdot\text{K})$ | $1.20\text{ W}/(\text{m}\cdot\text{K})$ | $0.00\text{ W}/(\text{m}\cdot\text{K})$ | Exact ($0.0$) | **PASSED** |
| **AISI 1018 Diffusivity $\alpha$** | $1.36 \times 10^{-5}\text{ m}^2/\text{s}$ | $1.36 \times 10^{-5}\text{ m}^2/\text{s}$ | $0.00\text{ m}^2/\text{s}$ | Exact ($0.0$) | **PASSED** |
| **Peak Excitation Flux $q_0$** | $5000\text{ W/m}^2$ | $5000\text{ W/m}^2$ | $0.00\text{ W/m}^2$ | Exact ($0.0$) | **PASSED** |
| **Front Surface Peak Temp $T_{\text{peak}}$** | $300.82\text{ K}$ | $300.71\text{ K}$ | $0.11\text{ K}$ | $< 0.50\text{ K}$ | **PASSED** |
| **Defect Center Time-RMS Difference** | — | — | $0.098\text{ K}$ | $< 0.25\text{ K}$ | **PASSED** |
| **Peak Contrast Amplitude $\Delta T$** | $1.45\text{ K}$ | $1.43\text{ K}$ | $0.02\text{ K}$ | $< 0.10\text{ K}$ | **PASSED** |
| **Matched Filter Correlation Peak Time** | $4.84\text{ s}$ | $4.84\text{ s}$ | $0.00\text{ s}$ | $< 0.05\text{ s}$ | **PASSED** |
| **SVD EOF1 Spatial Cosine Similarity** | $1.000$ | $0.9998$ | $0.0002$ | $< 0.01$ | **PASSED** |

---

## 3. Discretization & Solver Implementation Details

| Property | Python Implementation | MATLAB Implementation | Notes |
| :--- | :--- | :--- | :--- |
| **Spatial Discretization** | Conservative 3-D FDM / Hex mesh | Genuine 3-D Trilinear Hex8 FEM (Primary) + FDM (Secondary) | Pure MATLAB Hex8 FEM uses Kronecker analytical formulation |
| **Temporal Integration** | Implicit Euler / SciPy SuperLU Sparse solver | Implicit Euler / Cholesky Decomposition (`decomposition(A, 'chol', 'lower')`) | MATLAB leverages pre-factorized sparse Cholesky |
| **Matched Filtering** | `scipy.signal.fftconvolve` | Vectorized `conv2(T_ac, flipud(ref), 'same')` | Identical discrete cross-correlation mathematics |
| **SVD Decomposition** | `numpy.linalg.svd` / `scipy.sparse.linalg.svds` | Built-in `svds(X, K)` | Cosine similarity $> 0.999$ across leading EOFs |
| **Binarization** | `skimage.filters.threshold_otsu` | Native `graythresh` / Vectorized Otsu | Identical within 1 graylevel bin |
| **Coordinate Conventions** | $(y, x)$ NumPy matrix indexing | $(x, y)$ Cartesian coordinates mapped to $(row, col)$ | Standardized mapping maintained across both frameworks |

---

## 4. Conclusion

The MATLAB numerical engine achieves full scientific parity with the Python reference framework. The minor temperature discrepancy ($0.11\text{ K}$ at peak, $< 0.04\%$ relative error) is attributable to the continuous Galerkin Hex8 shape function integration in FEM compared to cell-centered finite volume/difference flux averaging.
