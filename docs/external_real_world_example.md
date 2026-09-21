# Real-World Measured Thermography Transfer Example on Mild Steel

> **SCIENTIFIC CLASSIFICATION & INTEGRITY DISCLAIMER**
> 
> - **Nature of this Dataset:** Measured laboratory pulsed-thermography data from an independent public repository (The Hong Kong Polytechnic University, DOI: [10.60933/PRDR/HJYNZB](https://doi.org/10.60933/PRDR/HJYNZB)).
> - **Specimen:** Mild steel plate ($150 \times 150 \times 10\text{ mm}$) containing manufactured circular and rectangular flat-bottom holes (corrosion/pipe-wall thinning surrogates).
> - **Excitation:** Optical flash pulse ($6\text{ kJ}$, $4\text{ ms}$).
> - **Purpose:** Demonstrates non-synthetic data ingestion architecture, confirms signal-processing pipeline compatibility with physical infrared camera sequences, and validates algorithm transfer under strict blind processing.
> - **EXPLICIT NON-CLAIMS:**
>   - This is **NOT** experimental LFMT validation.
>   - This is **NOT** real slag inclusion validation.
>   - This is **NOT** industrial or in-situ weld validation.
>   - The 4,030-evaluation LFMT slag benchmark remains a **rigorous numerical 3-D FEM simulation study**.

---

## 1. External Dataset Overview

| Field | Specification |
|:---|:---|
| **Dataset Title** | Thermal imaging dataset from mild steel plate inspected by pulsed thermography with interface differences |
| **DOI** | [10.60933/PRDR/HJYNZB](https://doi.org/10.60933/PRDR/HJYNZB) (Version 2.0, 2025-05-19) |
| **Repository** | PolyU Research Data Repository (Dataverse) |
| **Authors** | Samuel Yu, Winnie Wai-sze Chung, Tom Chun-wai Lau, Wallace Wai-lok Lai, Janet Fung Chu Sham, Chun Yiu Ho |
| **Affiliations** | The Hong Kong Polytechnic University / The Hong Kong and China Gas Company Limited |
| **License** | Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0) |
| **Specimen Material** | Mild steel plate ($150 \times 150 \times 10\text{ mm}$) |
| **Defect Geometry** | 11 circular flat-bottom holes (diameters $2\text{--}10\text{ mm}$, depths $0.5\text{--}5.0\text{ mm}$) |
| **Excitation Source** | Dual photographic flash units ($2 \times 3\text{ kJ} = 6\text{ kJ}$, $4\text{ ms}$ pulse duration) |
| **Infrared Camera** | FLIR A655sc uncooled microbolometer ($640 \times 480\text{ pixels}$, $\text{NETD} < 30\text{ mK}$, $7.5\text{--}14\ \mu\text{m}$ LWIR) |
| **Acquisition Rate** | $50.0\text{ Hz}$ native ($25.0\text{ Hz}$ subsampled for $20.0\text{ s}$ total sequence duration) |
| **Archive Ingested** | `MS-facq-50Hz-air-cir-1_0-999.zip` ($501,894,301\text{ bytes}$, SHA-256: `0e7fbce21f15df22463a1994122817ec7309619fb76fae74cdb477f043659718`) |

---

## 2. Ingestion & Radiometric Validation

The ingestion interface ([`src/lfmt/io_experimental.py`](file:///e:/lfmt-slag-detection/src/lfmt/io_experimental.py)) parses the individual frame CSV files, converts calibrated temperatures from Celsius to Kelvin ($T_{\text{K}} = T_{\text{C}} + 273.15$), and validates radiometric boundaries:

- **Ingested Matrix Dimensions:** $500\text{ frames} \times 480\text{ px} \times 640\text{ px}$
- **Sequence Duration:** $19.96\text{ s}$ (from $t = 0.00\text{ s}$ to $t = 19.96\text{ s}$)
- **Radiometric Span:**
  - Ambient baseline: $293.74\text{ K}$ ($20.59^\circ\text{C}$)
  - Peak flash temperature: $373.22\text{ K}$ ($100.07^\circ\text{C}$)
  - Sequence mean temperature: $295.97\text{ K}$ ($22.82^\circ\text{C}$)
- **Data Integrity:** $0$ dead frames, $0$ NaN values, strictly monotonic timestamps, SHA-256 archive fingerprint verified.

---

## 3. Signal Processing Pipeline & Blind Transfer Results

All algorithms were executed under **strict blind processing mode** without ground-truth masks, defect bounding boxes, or spatial priors.

### 3.1 Algorithm Configuration & Execution Summary

| Processing Method | Status | Mode / Criterion | Execution Time (s) | Key Transfer Output |
|:---|:---|:---|:---:|:---|
| **Raw Contrast** | Enabled | Blind max contrast frame | $1.729\text{ s}$ | Peak contrast detected at $t = 3.20\text{ s}$ (Frame 80) |
| **Matched Filter** | **Disabled** | N/A | N/A | Excluded: Excitation is pulsed flash, not LFMT chirp |
| **PCT** | Enabled | Blind excess kurtosis | $7.402\text{ s}$ | Selected EOF Mode #3 ($98.07\%$ variance in Mode 1) |
| **SPCT** | Enabled | Blind kurtosis ($\alpha = 0.05$) | $14.449\text{ s}$ | Selected Component #3 (sparsity ratio $= 79.05\%$) |
| **RPT** | Enabled | Gaussian projection ($d = 6$) | $2.442\text{ s}$ | Selected Component #4 (compression ratio $= 83.33\times$) |

```
                       REAL-WORLD EXTERNAL TRANSFER PIPELINE
 ┌─────────────────────────┐     ┌────────────────────────┐     ┌────────────────────────┐
 │   Calibrated Measured   │ ──> │   Pre-Flash Baseline   │ ──> │   Strict Blind Modes   │
 │   Radiometric Frames    │     │   Offset Subtraction   │     │  (Kurtosis / Sparsity) │
 │  (500 x 480 x 640 @25Hz)│     │     (Static ΔT)        │     │                        │
 └─────────────────────────┘     └────────────────────────┘     └───────────┬────────────┘
                                                                            │
             ┌──────────────────────┬───────────────────────┬───────────────┴───────────────┐
             ▼                      ▼                       ▼                               ▼
     ┌───────────────┐      ┌───────────────┐       ┌───────────────┐               ┌───────────────┐
     │ Raw Contrast  │      │   Blind PCT   │       │  Blind SPCT   │               │   Blind RPT   │
     │  (t = 3.20 s) │      │  (EOF Mode 3) │       │ (Comp 3, α=.05)│               │  (Comp 4, d=6)│
     └───────────────┘      └───────────────┘       └───────────────┘               └───────────────┘
```

---

## 4. Key Differences: Synthetic LFMT Slag vs Measured Pulsed FBH

| Physical Characteristic | Synthetic LFMT Slag Model (Simulation) | Measured External Plate (PolyU Dataset) |
|:---|:---|:---|
| **Excitation Modality** | LFMT linear frequency-modulated chirp ($0.01\text{--}0.50\text{ Hz}$, $10\text{ s}$) | Single flash pulse ($6\text{ kJ}$, $4\text{ ms}$) |
| **Thermal Penetration Depth** | Diffusion controlled by instantaneous modulation frequency $\mu = \sqrt{\frac{2\alpha}{\omega(t)}}$ | Diffusion governed by classical 1D cooling law $T(t) \propto t^{-1/2}$ |
| **Target Defect Type** | Subsurface non-metallic slag inclusion ($\kappa = 1.2\text{ W/m}\cdot\text{K}$, $\rho = 2800\text{ kg/m}^3$) | Manufactured flat-bottom cylindrical void (air interface) |
| **Defect Geometry** | Diameter $4\text{--}12\text{ mm}$, Depth $0.2\text{--}2.0\text{ mm}$ | Diameter $2\text{--}10\text{ mm}$, Depth $0.5\text{--}5.0\text{ mm}$ |
| **Matched Filter Suitability** | **Optimal** (chirp correlation extracts phase/depth profile) | **Not Applicable** (no reference chirp waveform present) |
| **PCT / SPCT Suitability** | Isolates progressive depth-dependent chirp phases | Isolates spatial decay modes from optical flash non-uniformity |

---

## 5. Standardized Template for Future Physical LFMT Experiments

To prepare for future physical LFMT laboratory experiments on actual mild-steel weld specimens with calibrated slag inclusions, the ingestion format is formalized in [`data/experimental_lfmt_slag/README_TEMPLATE.md`](file:///e:/lfmt-slag-detection/data/experimental_lfmt_slag/README_TEMPLATE.md).

Physical acquisitions should capture:
1. **Chirp Excitation Metadata:** Start frequency $f_0$, end frequency $f_1$, chirp duration $T_{\text{chirp}}$, optical/induction power (W).
2. **Camera Calibration:** NETD (mK), integration time ($\mu\text{s}$), spatial calibration (mm/pixel), emissivity setting.
3. **Specimen Metallography:** Base metal composition, weld bead geometry, X-ray CT ground-truth depth and volume measurements.
