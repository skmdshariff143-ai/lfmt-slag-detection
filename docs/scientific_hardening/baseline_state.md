# Scientific Hardening & Verification: Baseline State & Provenance Record

**Date:** 2026-09-20
**Repository:** `skmdshariff143-ai/lfmt-slag-detection`
**Active Working Branch:** `scientific-hardening-v3`

---

## 1. Baseline Git Commit Identification

| Reference Label | Commit SHA | Tracking / Location | Status |
|:---|:---|:---|:---|
| **main HEAD** | `d843955681120fdb41f0a9969c3a268a7373f76a` | `origin/main` | Production & Vercel live |
| **research-v2 HEAD** | `3b9ff94f31c5db9853926ea61427503b41315904` | `origin/research-v2` | Research V2 numerical gate passed |
| **conference-v1.0 Tag** | `0469c2b963162fb16bf7d84f8bb64f899042b936` | `tag: conference-v1.0` | Frozen historical benchmark baseline |
| **Production Deployment Commit** | `d843955681120fdb41f0a9969c3a268a7373f76a` | `https://web-kappa-woad-56.vercel.app` | Vercel production alias |

---

## 2. Divergence Analysis (main vs research-v2)

### Files Unique to `research-v2`:
- `configs/research_v2.yaml`, `configs/research_v2_split.yaml`
- `docs/research_v2/*` (all verification reports and taxonomies)
- `scripts/validate_fem_mesh.py`, `scripts/compare_fdm_fem_v2.py`, `scripts/run_research_v2_pilot.py`, `scripts/run_research_v2_ablation.py`, `scripts/analyze_failure_modes.py`
- `src/lfmt/io_experimental.py`, `src/lfmt/io/*`
- `tests/test_research_v2.py`

### Scientific Upgrades on `research-v2`:
1. **Adaptive Tensor-Graded FEM Hexahedral Mesh** (`src/lfmt/simulation/fem.py`): Resolves defect diameter with $\ge 10$ elements and cover with $\ge 5$ elements.
2. **Stefan-Boltzmann Broadband Radiometric Physics & FPA Camera Model** (`src/lfmt/noise.py`): Replaces ad-hoc scalar multiplication with true exitance, NETD, PSF blur, FPN, and ADC quantization.
3. **Multi-Defect Hungarian Matching & Neutral Evaluation Tiers** (`src/lfmt/detection.py`, `src/lfmt/metrics.py`): Implemented Tiers A (Frozen Legacy), B (Moderate), C (Strict), D (High-Overlap) with strict anti-leakage.

---

## 3. Provenance & Protection Guardrails
- `results/conference/final/` is **strictly read-only and preserved**.
- Corrected scientific outputs will be written exclusively to `results/corrected_v1_1/` and/or `results/research_v3/`.
- No experimental claims or industrial readiness claims will be made.
- Do not deploy to Vercel yet.
