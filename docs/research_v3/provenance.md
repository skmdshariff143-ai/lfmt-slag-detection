# Research V3 System Provenance and Reproducibility Baseline

**Date:** 2026-09-20T18:07:00+05:30  
**Repository:** `skmdshariff143-ai/lfmt-slag-detection`  
**Host Environment:** Windows 11 x64, Python 3.13.13  

---

## 1. Git Commit & Release Provenance

| Entity | Git Identifier / Tag | Commit SHA-1 Fingerprint | Verification Status | Notes |
|:---|:---|:---|:---:|:---|
| **Production Main Branch** | `main` | `d843955b3d5e6e5a847aa2fe851006334037de03` | Frozen & Locked | Contains production web portal deployed on Vercel |
| **Conference V1.0 Release** | `tag: conference-v1.0` | `0469c2b4d13e3db85ba186c36142721867dd1179` | Frozen & Audited | 4,030-evaluation simulation study, zero modifications permitted |
| **Research V2 Base** | `origin/research-v2` | `3b9ff94f5a846039b13735fb42861bae622bdfdd` | Verified Baseline | FEM-FDM cross-validation & initial high-fidelity grading |
| **Active Development Branch** | `scientific-hardening-v3` | `3b9ff94f5a846039b13735fb42861bae622bdfdd` | In Progress | Active working tree for Research V3 scientific hardening & AI platform |

---

## 2. Environment & Core Scientific Dependencies

| Package | Detected Version | Role in Platform |
|:---|:---:|:---|
| **Python** | `3.13.13` | Core runtime |
| **NumPy** | `2.4.6` | Numerical vectorization & array storage |
| **SciPy** | `1.18.0` | Sparse linear solvers (`SuperLU`), interpolation, signal processing |
| **scikit-fem** | `12.0.2` | 3D weak variational FEM assembly (`ElementHex1`) |
| **scikit-learn** | `1.6.0` | SVD/TruncatedSVD (PCT), SparsePCA (SPCT), Random Projection (RPT), ML baselines |
| **PyTorch** | `2.7.1+cpu` | Deep learning models (2D/3D CNNs, U-Net-lite, physics multi-task heads) |
| **FastAPI** | `0.140.0` | Asynchronous REST backend & scientific job orchestration |
| **Uvicorn** | `0.34.0` | ASGI web server |
| **Pydantic** | `2.14.0a1` | Data schema validation & config models |
| **Pandas** | `2.2.3` | High-throughput tabular CSV ingestion |
| **Matplotlib** | `3.10.1` | Publication-grade figure generation (300 DPI) |
| **ONNX / ONNX Runtime** | *Pending Install* | Edge CPU inference deployment benchmark |

---

## 3. Data Sources & Scientific Classification

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│ CATEGORY A: Numerical LFMT Slag-Inclusion Simulation Benchmark                                   │
│ Source: High-fidelity 3D FEM transient heat conduction on AISI 1018 mild steel plate              │
│ Status: Active benchmark in configs/research_v3_high_fidelity.yaml (Tensor graded mesh)          │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│ CATEGORY B: External Measured Thermography Transfer Study                                        │
│ Source: PolyU Mild Steel Pulsed Thermography Dataset (DOI: 10.60933/PRDR/HJYNZB, Version 2.0)    │
│ Specimen: 150 x 150 x 10 mm plate with 11 flat-bottom holes (corrosion surrogates, air void)     │
│ Excitation: 6 kJ optical flash pulse (NOT LFMT chirp)                                            │
│ Processing: Strict blind mode (Raw, PCT, SPCT, RPT). Matched Filter disabled.                     │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│ CATEGORY C: Physical LFMT Slag Validation                                                        │
│ Status: Future work / NOT YET PERFORMED. Explicitly documented across all project artifacts.     │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```
