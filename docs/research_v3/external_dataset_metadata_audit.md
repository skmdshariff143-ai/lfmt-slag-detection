# External Measured Thermography Dataset Metadata & Provenance Audit

**Audit Date:** 2026-09-20T18:09:00+05:30  
**Dataset Target:** PolyU Mild Steel Pulsed Thermography Dataset  
**DOI:** [10.60933/PRDR/HJYNZB](https://doi.org/10.60933/PRDR/HJYNZB) (Version 2.0, 2025-05-19)  
**Host Repository:** PolyU Research Data Repository (Dataverse)  

---

## 1. Ground-Truth Source Reconciliations

An exhaustive reconciliation between the published dataset source paper/manifest and the repository documentation was conducted to eliminate all ambiguities in specimen and defect dimensions:

| Parameter | Original Dataset Source Specification | Repository Discrepancies Found | Reconciled Canonical V3 Specification |
|:---|:---|:---|:---|
| **Specimen Material** | Mild steel plate | None | **Mild steel plate (structural grade)** |
| **Plate Dimensions** | $150.0 \times 150.0 \times 10.0\text{ mm}$ | None | **$150.0 \times 150.0 \times 10.0\text{ mm}$** |
| **Excitation Modality** | Flash optical pulsed thermography | None | **Optical flash pulse ($6\text{ kJ}$, $4\text{ ms}$)** |
| **Excitation Source** | Dual ELINCHROM ZOOM Pro HD ($2 \times 3\text{ kJ}$) | None | **Dual flash units ($6\text{ kJ}$ total energy)** |
| **Camera Model** | FLIR A655sc LWIR microbolometer ($7.5\text{--}14\ \mu\text{m}$) | None | **FLIR A655sc ($640 \times 480\text{ px}$, $\text{NETD} < 30\text{ mK}$)** |
| **Native Frame Rate** | $50.0\text{ Hz}$ | None | **$50.0\text{ Hz}$ ($25.0\text{ Hz}$ with $2\times$ subsampling)** |
| **Total Frames in Sequence** | 1,000 frames ($20.0\text{ s}$ total acquisition) | None | **1,000 frames native / 500 frames processed** |
| **Defect Geometry (Circular)** | 11 flat-bottom holes: diameters $5, 10, 15, 20\text{ mm}$; residual depths $1, 3, 5\text{ mm}$ | Early draft mentioned 2--10 mm | **Diameters $5, 10, 15, 20\text{ mm}$; depths $1, 3, 5\text{ mm}$** |
| **Defect Physical Nature** | Air-filled / sand-filled flat-bottom blind holes (corrosion surrogates) | None | **Manufactured flat-bottom holes (air void)** |
| **Source Data Format** | 1,000 CSV files containing $480 \times 640$ matrix in Celsius | None | **CSV in Celsius $\to$ converted to Kelvin ($T_{\text{K}} = T_{\text{C}} + 273.15$)** |
| **Archive Ingested** | `MS-facq-50Hz-air-cir-1_0-999.zip` ($501,894,301\text{ bytes}$) | None | **SHA-256: `0e7fbce21f15df22463a1994122817ec7309619fb76fae74cdb477f043659718`** |

---

## 2. Inconsistency Resolutions

1. **Defect Diameter Bounds:** Corrected all references from "$2\text{--}10\text{ mm}$" to the true physical range of the PolyU circular specimen: **$5.0\text{ to } 20.0\text{ mm}$ diameter**, with residual ligament depths of **$1.0, 3.0,\text{ and } 5.0\text{ mm}$**.
2. **Defect Physics Classification:** Re-emphasized that the PolyU specimen contains **machined cylindrical flat-bottom holes** designed to simulate localized pipe-wall thinning and corrosion loss. It is **NOT** a welding specimen and does **NOT** contain slag inclusions.
3. **Excitation Transfer Rule:** Re-confirmed that **Matched Filter is permanently disabled** for this dataset because the flash pulse excitation contains no modulated frequency chirp.
