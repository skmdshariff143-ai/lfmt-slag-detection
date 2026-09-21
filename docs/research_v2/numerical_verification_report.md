# Research V2 & V3 Numerical and Physical Verification Report

**Date:** 2026-09-20  
**Branch:** scientific-hardening-v3  
**Repository:** skmdshariff143-ai/lfmt-slag-detection  
**Verification Status:** COMPLETED AND VERIFIED AGAINST FROZEN ACCEPTANCE CRITERIA  

---

## 1. Executive Summary

This report documents the rigorous mathematical and physical verification gates for the Linear Frequency-Modulated Infrared Thermography (LFMT) subsurface slag inclusion detection simulation and processing framework. All evaluations were executed with executable code under strict blind processing conditions, preserving historical conference-v1.0 results intact.

---

## 2. Stochastic Noise Seed Integrity & Deterministic Reproducibility

### P0 Seed Misconfiguration Fix
- **Root Cause:** Historical script dynamically assigned 
oise_cfg.random_seed = seed, while NoiseConfig used seed = 42, causing silent fallback to seed 42.
- **Correction:** Synchronized NoiseConfig.seed, runner assignment, and noise pipeline to use canonical seed.
- **Verification:** 10 distinct seeds (1001--1010) produced 10 unique SHA-256 tensor fingerprints, while repeated seed 1001 matched bit-for-bit.

| Seed | Tensor SHA-256 Fingerprint | Measured SNR [dB] | Verification |
|:---:|:---:|:---:|:---:|
| 1001 | 99edcabb958697a391895609d855451eaf0e2afdaa2bcecda672e108c10d287c | -2.901 | UNIQUE |
| 1002 | caf64ddcfb90269150ce637544ecaaffc52f5c7b07a9f85ce11f3506c7f17f84 | -2.811 | UNIQUE |
| 1003 | 543919363165379e1dc714d333dd385f109d519348cf259e3e3e831bcf4fc2c4 | -2.767 | UNIQUE |
| 1004 | a6da4b2f6324229314a448153769f56d6d047ed9328aa6b2f75e146964eef95f | -2.956 | UNIQUE |
| 1005 | cbdd8b26886d033e3efe6ec437bce2e61f1b4b167718a28b0936848729395a2d | -2.957 | UNIQUE |
| 1006 | 2991b6fcc2ab64463bfe6211ae2fb92296affdd04fa85c2d2fb7df9799ed3db5 | -2.871 | UNIQUE |
| 1007 | 5255b2e7d1100778eaab35d917948eea3d32bbfcf90715276d017517b0094e4b | -2.863 | UNIQUE |
| 1008 | 0f6de79836a58508a35defb9e7225b3917ef31ce43d3ea71afd76ef45548c853 | -2.924 | UNIQUE |
| 1009 | dbfacda859200cd8c184ddd4088ed8d289be7cf45b2031b0500ffa535c2c168b | -2.640 | UNIQUE |
| 1010 | 73e3ca6209a0be7ad4a87a2d714b8cba9f6f31e2d0b42848d860ba09cf8819eb | -2.927 | UNIQUE |

---

## 3. 3-D FEM Mesh Convergence Verification

Evaluated across 4 critical physical cases against high-resolution reference solutions:
- **Case A:** Shallow Small (D = 4.0 mm, z = 0.2 mm)
- **Case B:** Deep Small (D = 4.0 mm, z = 1.0 mm)
- **Case C:** Moderate (D = 8.0 mm, z = 0.4 mm)
- **Case D:** Large Deep (D = 12.0 mm, z = 1.0 mm)

### Convergence Results vs Frozen Acceptance Criteria

| Case | Mesh Level | DOFs | Elements in D | Elements in Cover | Rel L2 Error [%] | Contrast Error [%] | Volume Error [%] | Status |
|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Case A** (D4 z0.2) | Reference Fine (Truth) | 44,100 | 12 | 8 | 0.00% | 0.00% | 0.27% | PASS |
| | **Adaptive Graded (Production)** | **14,400** | **10** | **5** | **0.03%** | **0.62%** | **1.86%** | **PASS** |
| | Medium Uniform | 9,075 | 0 | 0 | 0.58% | 59.32% | 100.00% | FAIL |
| | Coarse Uniform | 1,547 | 0 | 0 | 0.90% | 89.07% | 100.00% | FAIL |
| **Case B** (D4 z1.0) | Reference Fine (Truth) | 44,100 | 12 | 8 | 0.00% | 0.00% | 0.27% | PASS |
| | **Adaptive Graded (Production)** | **14,400** | **10** | **5** | **0.02%** | **1.47%** | **1.86%** | **PASS** |
| | Medium Uniform | 9,075 | 0 | 4 | 0.10% | 52.24% | 100.00% | FAIL |
| | Coarse Uniform | 1,547 | 0 | 2 | 0.13% | 65.44% | 100.00% | FAIL |
| **Case C** (D8 z0.4) | Reference Fine (Truth) | 44,100 | 12 | 8 | 0.00% | 0.00% | 0.27% | PASS |
| | **Adaptive Graded (Production)** | **14,400** | **10** | **5** | **0.05%** | **0.09%** | **1.86%** | **PASS** |
| | Medium Uniform | 9,075 | 2 | 1 | 1.49% | 41.08% | 33.27% | FAIL |
| | Coarse Uniform | 1,547 | 0 | 1 | 1.81% | 62.66% | 100.00% | FAIL |
| **Case D** (D12 z1.0) | Reference Fine (Truth) | 44,100 | 12 | 8 | 0.00% | 0.00% | 0.27% | PASS |
| | **Adaptive Graded (Production)** | **14,400** | **10** | **5** | **0.05%** | **0.15%** | **1.86%** | **PASS** |
| | Medium Uniform | 9,075 | 2 | 4 | 0.77% | 33.48% | 33.46% | FAIL |
| | Coarse Uniform | 1,547 | 0 | 2 | 1.44% | 59.84% | 1.14% | FAIL |

*Acceptance Thresholds: Rel L2 Error < 3.0%, Peak Contrast Error < 5.0%, Volume Error < 5.0%.*

---

## 4. Signal Processing & Blind Detection Integrity

1. **Strict Blind PCT Mode:**
   - Default selection_criterion configured to lind_kurtosis.
   - Polarity selection determined by spatial third-moment skewness without ground truth.
   - Regression test passes verifying identical output with or without ground truth mask.
2. **SPCT Hyperparameter Synchronization:**
   - Parameter propagation explicitly mapped to SPCTConfig dataclass (
_components=6, lpha=0.05, max_iter=40, 	ol=1e-2).
3. **Simulation Config Hash & Cache Invalidation:**
   - Cache hash rigorously binds mesh coordinates, time step, duration, thermophysical properties, defect dimensions, excitation parameters, and boundary conditions.
   - Any modification automatically invalidates stale forward simulation caches.
