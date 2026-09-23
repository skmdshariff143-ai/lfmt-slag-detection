# Release Notes: Research V3 Scientific & Simulation Platform

**Release Version:** `3.0.0-research`  
**Target Branch:** `scientific-hardening-v3`  

---

## 🚀 Key Features & Architectural Enhancements

### 1. Dual-Backend 3-D Thermal Simulation
- **Python FEM Backend**: 3-D weak variational formulation using `scikit-fem` with trilinear hexahedral elements (`ElementHex1`), implicit Euler time-stepping, and pre-factored SuperLU sparse solvers.
- **MATLAB FDM Backend (`MATLAB_FDM`)**: 3-D conservative flux finite-difference solver (`lfmt_simulate_fdm.m`) with harmonic mean interface conductivities, automated Courant stability sub-stepping, and Robin radiation/convection boundary conditions.
- **Numerical Cross-Validation**: Both solvers cross-validated with $<0.25\%$ relative $L_2$ error.

### 2. Verified Example Reference Library (Milestone 1)
- Standardized, cryptographically verified (`sha256.txt`) thermography reference samples:
  - `healthy_lfmt`: Homogeneous negative control plate ($0.05-0.50\text{ Hz}$ chirp).
  - `slag_shallow`: $D = 8\text{ mm}, d = 0.4\text{ mm}$ slag inclusion in mild steel.
  - `slag_deep`: $D = 8\text{ mm}, d = 0.8\text{ mm}$ slag inclusion in mild steel.
  - `multi_slag`: Dual spatially disjoint slag inclusions ($D = 6.0\text{ mm}$ and $4.8\text{ mm}$).
  - `single_thermal_frame`: Single 2-D spatial thermal snapshot ($t = 8.0\text{ s}$).
  - `measured_polyu_preview`: External measured flash pulsed thermography on mild steel (PolyU benchmark).

### 3. Decoupled Dual-Mode Demonstration
- **Local Live Mode (`scripts/demo/start_local_demo.ps1`)**: Live execution via FastAPI (`localhost:8000`) and MATLAB Engine R2026a.
- **Hosted Vercel Mode**: Serverless frontend deployment on Vercel with automatic fallback to precomputed numerical simulation (`web/public/demo/matlab_shallow_slag.json`), eliminating localhost connection errors.

### 4. Comprehensive NDT Signal Processing
- Multi-modality feature extraction: Raw Contrast, Vectorized FFT Matched Filter, Principal Component Thermography (PCT), Sparse PCA Thermography (SPCT), and Random Projection Technique (RPT).
- Autonomous Otsu segmentation, multi-method voting, and strict ground truth / prediction isolation.

### 5. Scientific CI & Cross-Platform Normalization
- Portable GitHub Actions matrix across Python 3.10, 3.11, and 3.12 (86 portable tests passing with zero dependencies on MATLAB).
- Cross-platform line-ending checksum normalization (`.gitattributes`).
- Automated frontend typechecking, linting, and 19-route static page generation.

---

## ⚠️ Known Limitations & Boundary Guardrails
1. **MATLAB on Edge/Vercel**: Live MATLAB simulation is unavailable by design on Vercel; live execution requires a local MATLAB installation.
2. **AI Safety Gate**: Untrained deep learning classification is explicitly gated; anomaly detection is formulated strictly from physics-based thermal processing consensus.
3. **Physical LFMT Validation**: Physical laboratory LFMT chirp testing on welded mild steel plates (Category C) remains future work.
