# Intelligent Thermographic Defect Analyzer: Architecture & Scientific Implementation Strategy

**Date:** 2026-09-20T19:48:00+05:30  
**Author:** Principal Research Engineer, Scientific Software Architect & AI Lead  
**Active Working Tree:** `scientific-hardening-v3`  

---

## 1. Executive Summary

The **Intelligent Thermographic Defect Analyzer** is a multi-modal, physics-informed, autonomous NDT diagnosis engine designed to accept arbitrary thermographic inputs (single frames, video stacks, CSVs, MAT, NPY/NPZ, TIFF, and numerical simulation outputs) and execute an end-to-end scientific analysis:

```
                  INTELLIGENT DEFECT ANALYZER PIPELINE
 ┌───────────────────────┐     ┌───────────────────────┐     ┌───────────────────────┐
 │   Arbitrary Upload    │ ──> │ Universal Input Type  │ ──> │ Physical & Radiometric│
 │ (Image/Stack/NPY/MAT) │     │     & FOV Detector    │     │       Validator       │
 └───────────────────────┘     └───────────────────────┘     └───────────┬───────────┘
                                                                         │
 ┌───────────────────────┐     ┌───────────────────────┐     ┌───────────▼───────────┐
 │  Universal Automated  │ <── │ Scientific Method     │ <── │ Input Representation  │
 │     Preprocessing     │     │ Applicability Engine  │     │ (Kelvin/Radiance/Raw) │
 └──────────┬────────────┘     └───────────────────────┘     └───────────────────────┘
            │
            ├──────────────────────┬───────────────────────┬─────────────────────────┐
            ▼                      ▼                       ▼                         ▼
 ┌──────────────────────┐ ┌──────────────────────┐ ┌──────────────────────┐ ┌───────────────────────┐
 │  Raw Contrast & ΔT   │ │   Blind PCT Modes    │ │      Blind SPCT      │ │   LFMT Pulse Comp.    │
 │ (Peak Contrast Time) │ │   (Excess Kurtosis)  │ │   (Sparse Features)  │ │ (LFMT Chirp Only!)  │
 └──────────┬───────────┘ └──────────┬───────────┘ └──────────┬───────────┘ └───────────┬───────────┘
            │                        │                        │                         │
            └──────────────────────┬─┴────────────────────────┴─────────────────────────┘
                                   │
                                   ▼
 ┌──────────────────────────────────────────────────────────────────────────────────────────┐
 │ Physics & Statistical Feature Engine (Diffusivity, Effusivity, μ(f), Gradients, Slopes)  │
 └─────────────────────────────────────────┬────────────────────────────────────────────────┘
                                           │
 ┌─────────────────────────────────────────▼────────────────────────────────────────────────┐
 │ Multi-Task AI Engine (Classical ML + Deep Spatial/Temporal CNNs + U-Net-lite)            │
 └─────────────────────────────────────────┬────────────────────────────────────────────────┘
                                           │
 ┌─────────────────────────────────────────▼────────────────────────────────────────────────┐
 │ Multi-Method Consensus & Agreement Fusion (Uncertainty + Epistemic MC Dropout + OOD)     │
 └─────────────────────────────────────────┬────────────────────────────────────────────────┘
                                           │
                                           ▼
 ┌──────────────────────────────────────────────────────────────────────────────────────────┐
 │ Structured Defect Report (Type, Depth, Diameter, Centroid, Confidence, Explanation, PDF) │
 └──────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Current State vs Target State Audit

| System Area | Existing Repository Capabilities | Target Analyzer Capabilities |
|:---|:---|:---|
| **Input Ingestion** | `io_experimental.py` loads NumPy, MAT, and CSV zip archives. | Universal file inspector auto-detecting single frames, multi-stacks, TIFF, MP4, CSVs, MAT, NPY, NPZ, and simulation outputs. |
| **Physical Units** | Kelvin / Celsius converted with static assumptions. | Formal classification into `RADIOMETRIC_TEMPERATURE`, `RADIANCE`, `RAW_SENSOR_COUNTS`, `NORMALIZED_INTENSITY`, `VISIBLE_IMAGE`, `UNKNOWN`. |
| **Applicability Logic** | Manual script execution per dataset. | Autonomous rules engine determining scientific compatibility for every technique with explicit `APPLICABLE`, `NOT_APPLICABLE`, or `INSUFFICIENT_METADATA` reasons. |
| **Signal Processing** | Raw Contrast, Matched Filter, Blind PCT, SPCT, RPT verified. | Dynamically dispatched based on applicability; single-image spatial fallbacks for single frames; pulse compression strictly guarded. |
| **AI Defect Detection** | Planned for Research V3. | Classical ML baseline + Spatial 2D CNN + Temporal sequence model + U-Net segmentation + Physics Multi-Task Head. |
| **Uncertainty & OOD** | None. | MC Dropout epistemic uncertainty + Mahalanobis/Energy OOD detector flagging unvalidated inputs. |
| **Defect Taxonomy** | Binary slag inclusion. | Hierarchical classifier: Healthy $\to$ Anomaly $\to$ Subsurface Anomaly $\to$ Specific Class (`SLAG_INCLUSION`, `WALL_THINNING`, `AIR_VOID`, `UNKNOWN`). |
| **Backend & API** | Standalone CLI scripts. | FastAPI REST asynchronous service (`/api/v1/analyze/*`) with progress tracking and job dispatch. |
| **Web Interface** | Next.js presentation portal (`/conference`, `/explorer`). | Interactive `/analyze` diagnostic cockpit with drag-and-drop upload, synced map scrubbers, and PDF export. |

---

## 3. Scientific Compatibility Matrix

| Input Modality | $N_{\text{frames}}$ | Raw Contrast | Matched Filter | Blind PCT | Blind SPCT | Blind RPT | Spatial CNN | Temporal AI | Physics Features | Depth Sizing |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **LFMT Simulation Cube** | $\ge 100$ | ✅ | ✅ (Chirp Ref) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ (Calibrated) |
| **External Pulsed Thermogram** | $\ge 100$ | ✅ | ❌ (No Chirp) | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ (No Mod.) | ⚠️ (Surrogate) |
| **Uncalibrated Thermal Sequence** | $\ge 10$ | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ (No Units) | ❌ |
| **Single Calibrated Thermal Frame** | $1$ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ⚠️ (Static) | ❌ |
| **Ordinary RGB Photograph** | $1$ | ❌ | ❌ | ❌ | ❌ | ❌ | ⚠️ (Visual) | ❌ | ❌ | ❌ |

---

## 4. Proposed `AutoDefectAnalyzer` Software Architecture

```
src/lfmt/
├── io/
│   ├── __init__.py
│   ├── input_analyzer.py        # Universal file format & representation inspector
│   └── experimental.py          # Low-level array & archive loaders
├── analysis/
│   ├── __init__.py
│   ├── method_selector.py       # Scientific applicability & capability engine
│   ├── preprocessing.py         # Baseline correction, detrending, dead-pixel fixes
│   ├── physics_features.py      # Diffusivity, effusivity, diffusion depth, gradients
│   ├── single_frame.py          # Spatial contrast, morphology & texture for 1-frame
│   └── analyzer.py              # Master AutoDefectAnalyzer orchestrator
└── reporting/
    ├── __init__.py
    └── report_generator.py      # Automated PDF, JSON, and PNG artifact generator

ml/
├── __init__.py
├── models/
│   ├── __init__.py
│   ├── classical.py             # RandomForest, ExtraTrees, HistGradientBoosting
│   ├── deep_learning.py         # 2D CNN, Temporal CNN, U-Net-lite segmentation
│   └── multitask.py             # Physics-Informed Multi-Task Head Network
├── uncertainty/
│   ├── __init__.py
│   └── dropout.py               # Monte Carlo Dropout epistemic uncertainty engine
├── ood/
│   ├── __init__.py
│   └── detector.py              # Mahalanobis / Energy score OOD detector
└── fusion/
    ├── __init__.py
    └── consensus.py             # Multi-method calibrated agreement & consensus engine

api/
├── __init__.py
├── main.py                      # FastAPI application entrypoint
├── schemas/
│   ├── __init__.py
│   └── analysis.py              # Pydantic request/response data contracts
└── routes/
    ├── __init__.py
    └── analyze.py               # /api/v1/analyze endpoints
```
