# Linear Frequency-Modulated Infrared Thermography for Subsurface Slag Inclusion Detection in Mild Steel

[![CI Test Suite](https://github.com/skmdshariff143-ai/lfmt-slag-detection/actions/workflows/ci.yml/badge.svg)](https://github.com/skmdshariff143-ai/lfmt-slag-detection/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.10+](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue.svg)](https://www.python.org/)
[![MATLAB: R2026a](https://img.shields.io/badge/MATLAB-R2026a%20(Update%204)-orange.svg)](https://www.mathworks.com/products/matlab.html)
[![Next.js: 14](https://img.shields.io/badge/Next.js-14.2-black.svg)](https://nextjs.org/)

A research-grade computational, simulation, and non-destructive testing (NDT) platform for detecting, sizing, and localizing subsurface **welding slag inclusions** in structural **mild steel plates** using **Linear Frequency-Modulated Thermography (LFMT)**.

---

## ⚡ Quick Start: Dual-Mode Execution

### Option A: Local Professional Live Demo (FastAPI + MATLAB Engine)
To run the full stack with **live 3-D MATLAB thermal simulation**:
```powershell
# In PowerShell from repository root:
powershell -ExecutionPolicy Bypass -File scripts/demo/start_local_demo.ps1
```
- **Next.js Web Portal**: [`http://localhost:3000`](http://localhost:3000)
- **Simulation Lab**: [`http://localhost:3000/simulate`](http://localhost:3000/simulate)
- **FastAPI Backend**: [`http://localhost:8000`](http://localhost:8000)
- **Interactive API Docs**: [`http://localhost:8000/api/docs`](http://localhost:8000/api/docs)

### Option B: Hosted Vercel Preview (Frontend + Precomputed Demonstration)
- **Hosted Portal**: Deployable on Vercel (`Root Directory: web`).
- **Hosted Simulation Lab (`/simulate`)**: Automatically serves the verified **Precomputed MATLAB Numerical Simulation** (`web/public/demo/matlab_shallow_slag.json`) with full 101-frame surface thermogram animations, cooling curves, and multi-method NDT processing maps without requiring a local MATLAB installation.

> [!NOTE]
> **Operational Scope**: Live MATLAB simulation runs locally on MATLAB-capable workstations. Live MATLAB execution inside Vercel is **UNAVAILABLE BY DESIGN**.

---

## 🔬 Dual Simulation Backends & Numerical Cross-Validation

| Feature | Python FEM Backend | MATLAB FDM Backend (`MATLAB_FDM`) |
| :--- | :--- | :--- |
| **Formulation** | 3-D Weak Variational Form ($M \dot{T} + K T = F$) | 3-D Conservative Flux Discretization |
| **Spatial Elements** | Trilinear 8-node Hexahedral (`scikit-fem` `ElementHex1`) | Non-uniform 7-point Laplacian Finite-Difference Stencils |
| **Material Interfaces** | Continuous piecewise bilinear volumetric assembly | Harmonic mean conductivities $k_{i+1/2} = \frac{2 k_i k_{i+1}}{k_i + k_{i+1}}$ |
| **Time Integration** | Unconditionally stable Implicit Euler (SuperLU) | Automated Courant sub-stepping + vectorized Numba/MATLAB |
| **Cross-Validation** | Baseline reference solver | $<0.25\%$ relative $L_2$ error agreement with Python FEM |

---

## 📐 Research Problem & LFMT Physics

During shielded metal arc welding (SMAW) and flux-cored arc welding (FCAW), non-metallic **slag inclusions** (silicates) can become entrapped in the steel substrate. Severe thermal conductivity disparity ($k_{\text{steel}} \approx 51.9\text{ W/(m}\cdot\text{K)}$ vs $k_{\text{slag}} \approx 1.20\text{ W/(m}\cdot\text{K)}$) creates localized heat accumulation under transient surface heating.

### LFMT Chirp Waveform
The active excitation sweeps across frequencies $f_0 \to f_1$ ($0.05 \to 0.50\text{ Hz}$ over $10\text{ s}$):
$$q(t) = q_0 \cdot \frac{1 + \sin\left(2\pi \left(f_0 t + \frac{f_1 - f_0}{2 t_{\text{dur}}} t^2\right)\right)}{2}$$

---

## 📊 Autonomous NDT Signal Processing Pipeline

```
SURFACE THERMOGRAM SEQUENCE T(x,y,t)
               │
   ┌───────────┼───────────┬───────────┬───────────┐
   ▼           ▼           ▼           ▼           ▼
[ RAW ]     [ MF ]      [ PCT ]     [ SPCT ]    [ RPT ]
ΔT(t)     Vectorized   SVD / EOF    Sparse PCA   Random
Contrast  FFT Chirp    Subspace    Coordinate   Gaussian
Profiles  Correlation  Selection   Descent      Embeddings
   │           │           │           │           │
   └───────────┴─────┬─────┴───────────┴───────────┘
                     ▼
       ADAPTIVE OTSU SEGMENTATION
                     ▼
      MULTI-METHOD CONSENSUS VOTING
                     ▼
     ISOLATED SUBSURFACE DEFECT ANOMALY
```

---

## 📦 Verified Reference Example Library (Milestone 1)

Standardized reference cases with deterministic SHA-256 integrity manifests:
- `healthy_lfmt`: Homogeneous AISI 1018 mild steel (Negative control).
- `slag_shallow`: Subsurface slag inclusion ($D = 8.0\text{ mm}, d = 0.4\text{ mm}$).
- `slag_deep`: Subsurface slag inclusion ($D = 8.0\text{ mm}, d = 0.8\text{ mm}$).
- `multi_slag`: Dual disjoint slag inclusions ($D = 6.0\text{ mm}$ and $4.8\text{ mm}$).
- `single_thermal_frame`: Single 2-D spatial snapshot ($t = 8.0\text{ s}$).
- `measured_polyu_preview`: External measured flash pulsed thermography on mild steel.

---

## 🏛️ Repository Architecture

```
lfmt-slag-detection/
├── api/                       # FastAPI REST backend (/simulate, /analyze, /examples)
├── src/lfmt/                  # Core Python package (FEM, processing, materials, data)
├── matlab/                    # High-performance MATLAB core (lfmt_simulate_fdm.m, tests)
├── ml/                        # Physics-informed DL models & ONNX exporter
├── web/                       # Next.js 14 Web Portal (19 application routes)
├── data/examples/             # Verified reference thermogram library
├── docs/                      # Scientific documentation, MATLAB setup, & deployment guides
├── results/                   # Audited conference benchmark dataset (4,030 runs)
├── scripts/                   # Verification, benchmark, and demo launcher scripts
└── tests/                     # Pytest suite (portable unit tests + MATLAB integration)
```

---

## 🧪 Testing & Scientific Verification

```bash
# 1. Run portable Python test suite (86+ tests, zero MATLAB dependencies)
pytest -m "not matlab" -v

# 2. Run local MATLAB integration tests (on machines with MATLAB installed)
pytest -m matlab -v

# 3. Run standalone MATLAB unit tests
matlab -batch "addpath('matlab'); results=runtests('matlab/tests'); assertSuccess(results)"

# 4. Verify Next.js frontend
cd web && npm ci && npm run typecheck && npm run lint && npm run build
```

---

## ⚠️ Scientific Boundaries & Guardrails
1. **AI Safety Gate**: Deep learning classifiers are explicitly gated when unvalidated; defect isolation relies strictly on physics-based multi-method signal processing consensus.
2. **Ground Truth Isolation**: Ground truth geometry files are strictly inaccessible during blind inference evaluation.
3. **Category C Physical Validation**: Physical laboratory LFMT testing on welded specimens is documented as future work.

---

## 📄 Academic Citation & License
```bibtex
@software{lfmt_slag_detection_2026,
  title  = {Linear Frequency-Modulated Infrared Thermography for Subsurface Slag Inclusion Detection in Mild Steel},
  author = {Research Team},
  year   = {2026},
  url    = {https://github.com/skmdshariff143-ai/lfmt-slag-detection}
}
```
Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for details.