# Research V3 — Scientific Claims & Provenance Guardrails Matrix

| Document Version | Status | Active Git Branch | Commit SHA Baseline |
| :--- | :--- | :--- | :--- |
| **v3.0.0-final** | **VERIFIED & AUDITED** | `scientific-hardening-v3` | `3b9ff94...` |

---

## 1. Strict Three-Category Terminology Taxonomy

To guarantee unimpeachable scientific integrity and prevent overclaiming, all algorithms, web interfaces, FastAPI schemas, publications, and reports strictly adhere to this standardized tripartite categorization:

```
                               ┌─────────────────────────────────────────────────────────┐
                               │       RESEARCH PLATFORM SCIENTIFIC PROVENANCE           │
                               └────────────────────────────┬────────────────────────────┘
                                                            │
                 ┌──────────────────────────────────────────┼──────────────────────────────────────────┐
                 │                                          │                                          │
                 ▼                                          ▼                                          ▼
   ┌───────────────────────────┐              ┌───────────────────────────┐              ┌───────────────────────────┐
   │        CATEGORY A         │              │        CATEGORY B         │              │        CATEGORY C         │
   │  Numerical LFMT Slag      │              │  External Measured Flash  │              │  Physical LFMT Slag       │
   │  Inclusion Simulation     │              │  Transfer Study (PolyU)   │              │  Validation               │
   └─────────────┬─────────────┘              └─────────────┬─────────────┘              └─────────────┬─────────────┘
                 │                                          │                                          │
                 ▼                                          ▼                                          ▼
   • 3D FEM Heat Equation                     • Hong Kong PolyU Dataset                  • Physical LFMT laser/lamp
   • 4,030-evaluation audit                   • 150x150x10 mm steel plate                • Slag inclusion specimens
   • Chirp 0.05-0.50 Hz                       • 11 Flat-Bottom Holes (FBH)               • Calibrated IR radiometer
   • Frozen conference-v1.0                   • Optical Flash Pulse (Non-LFMT)           • STATUS: NOT YET PERFORMED
   • Fully Verified Benchmark                 • Blind Transfer Demonstration             • Future physical research
```

---

## 2. Detailed Category Claims Breakdown

| Dimension | Category A: Numerical LFMT Slag Benchmark | Category B: External Measured Transfer Study | Category C: Physical LFMT Slag Validation |
| :--- | :--- | :--- | :--- |
| **Material** | Mild Steel ($k=51.9\text{ W/m}\cdot\text{K}$, $\rho=7850\text{ kg/m}^3$) | Mild Steel ($150\times 150\times 10\text{ mm}$ Plate) | Mild Steel Weldment with Slag Inclusions |
| **Defect Type** | Subsurface Welding Slag Inclusions ($k=1.5\text{ W/m}\cdot\text{K}$) | 11 Flat-Bottom Holes (FBH: $D=5\text{--}20\text{ mm}, z=1\text{--}5\text{ mm}$) | Real Subsurface Welding Slag Inclusions |
| **Excitation** | Linear Frequency-Modulated Chirp ($0.05\text{--}0.50\text{ Hz}$) | Optical Flash Pulse (50 Hz frame acquisition) | Linear Frequency-Modulated Chirp ($0.05\text{--}0.50\text{ Hz}$) |
| **Source Type** | High-Fidelity 3D Finite Element Simulation | Real Infrared Radiometer Camera (Hong Kong PolyU) | Real Laboratory / Industrial Thermography |
| **Algorithms Evaluated** | Raw Contrast, Matched Filter, PCT, SPCT, RPT | Raw Contrast, Blind PCT, SPCT, RPT, Single-Frame Spatial | All applicable algorithms |
| **Matched Filter Status** | **ENABLED** (Chirp reference matches source) | **STRICTLY DISABLED & GUARDED** (Pulse is non-LFMT) | Enabled when physical chirp is applied |
| **Scientific Claim** | Defensible numerical sensitivity & algorithmic benchmark | Demonstrates pipeline ingestion & cross-domain transfer | **Explicitly NOT claimed; reserved for future work** |

---

## 3. Algorithmic Guardrail Verification

### 3.1 Blind Processing Rule
- **Rule:** Ground-truth defect locations, depths, and diameters must NEVER be accessed during preprocessing, component selection, threshold determination, or inference.
- **Verification:**
  - `RawThermalContrast` operates in blind maximum spatial variance mode.
  - `PrincipalComponentThermography` selects optimal EOFs via maximum spatial excess kurtosis (`blind_kurtosis`).
  - `SparsePrincipalComponentThermography` and `RandomProjectionTechnique` select components via blind kurtosis and contrast without spatial priors.
  - Hungarian bipartite matching is executed *strictly post-hoc* for validation scoring.

### 3.2 Matched Filter Invalidation Guardrail
- **Rule:** The LFMT Matched Filter mathematically requires a phase-coherent chirp excitation reference. When applied to pulsed thermography (Category B) or static single frames, the filter is fundamentally inapplicable.
- **Verification:** `MethodApplicabilityEngine` actively checks `excitation_metadata`. If excitation is pulsed or single-frame, Matched Filter is assigned `MethodStatus.INAPPLICABLE` and physically disabled.

### 3.3 Noise Floor & False Positive Rejection
- **Rule:** Healthy homogeneous plates (without inclusions) must reliably output `likely_defect_type = "HEALTHY"` with $P \ge 0.85$ and reject spurious noise peaks.
- **Verification:** Consensus engine integrates physical temperature elevation thresholds ($\Delta T \ge 0.15\text{ K}$) and statistical prominence thresholds ($z \ge 5.0$), ensuring zero false positives on Gaussian sensor noise.

---

## 4. Summary Table of Verified Commit SHAs & Datasets

| Dataset / Asset | Path | Hash / Checksum | Status |
| :--- | :--- | :--- | :--- |
| **Conference V1.0 Results** | `results/conference/final/raw_results_final.csv` | Frozen SHA | Audited & Protected |
| **PolyU Measured Archive** | `data/real_world_external/polyu_mild_steel_pulsed/` | External Public Dataset | Ingested & Verified |
| **Multi-Task Synthetic Prior** | `data/datasets/synthetic_multitask_lfmt/` | 260 Samples (.npz) | Generated & Tested |
| **FastAPI REST Service** | `api/main.py` + `api/routes/analyze.py` | Full Pytest Suite | 100% Passing (10/10) |
| **Next.js Web Portal** | `web/src/app/analyze/page.tsx` | Production Build | 100% Compiled (18/18) |
