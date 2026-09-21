# External Measured Mild-Steel Pulsed-Thermography Transfer Example

## Scientific Provenance & Classification
- **Dataset Title:** Thermal imaging dataset from mild steel plate inspected by pulsed thermography with interface differences
- **Repository:** PolyU Research Data Repository
- **DOI:** [10.60933/PRDR/HJYNZB](https://doi.org/10.60933/PRDR/HJYNZB)
- **Version:** 2.0 (Publication Date: 2025-05-19)
- **License:** CC BY-NC 4.0 (Creative Commons Attribution-NonCommercial 4.0 International)
- **Scientific Classification:** **External measured pulsed-thermography transfer example on mild steel**

---

## CRITICAL SCIENTIFIC DISCLAIMER
> [!IMPORTANT]
> **THIS IS REAL MEASURED EXPERIMENTAL DATA, BUT IT IS NOT LFMT AND DOES NOT CONTAIN SLAG INCLUSIONS.**
>
> 1. **Excitation:** This dataset uses **optical flash pulsed thermography** (4 ms, 6 kJ pulse), **NOT** Linear Frequency-Modulated (LFMT) chirp excitation.
> 2. **Defect Geometry & Material:** Defects are **manufactured flat-bottom holes** (air/sand surrogates for pipe-wall thinning/corrosion), **NOT** volumetric welding slag silicate inclusions embedded in welded joints.
> 3. **Specimen Geometry:** Specimen is a **10 mm thick mild steel plate**, whereas the primary LFMT simulation study investigates a **2.3 mm mild steel plate**.
> 4. **Scope & Purpose:** This dataset is utilized strictly to verify **data-ingestion architecture, loader compatibility, and algorithm transfer** (Raw Contrast, PCT, SPCT, RPT) on non-synthetic laboratory thermal sequences.
> 5. **Negative Claim:** This integration **DOES NOT** constitute experimental validation of LFMT slag detection.

---

## Specimen & Experimental Setup
- **Specimen:**  \times 150 \times 10$ mm mild steel plate with 11 circular flat-bottom holes (diameters 5, 10, 15, 20 mm; residual ligament thicknesses 1, 3, 5 mm).
- **Camera:** FLIR A655sc ( \times 480$ pixels, 50 Hz frame rate, .5 - 14\ \mu\text{m}$, NETD $< 30$ mK).
- **Excitation:** Rear-surface optical flash pulse (ELINCHROM ZOOM Pro HD, 6 kJ total energy).
