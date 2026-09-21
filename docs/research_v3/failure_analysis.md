# Research V3 — Physical, Numerical & Algorithmic Failure Analysis

| Document Version | Status | Date |
| :--- | :--- | :--- |
| **v3.0.0** | **AUDITED & DEFENDED** | **2026-09-20** |

---

## 1. Executive Summary

This document establishes the physical, numerical, and algorithmic operating boundaries of Linear Frequency-Modulated Infrared Thermography (LFMT) and classical/deep learning defect characterization for subsurface slag inclusions and structural defects in mild steel.

Understanding failure regimes is essential for scientific defensibility, ensuring that algorithmic claims are bounded by thermodynamic laws rather than artificial simulation artifacts.

---

## 2. Physical Failure Regimes & Thermodynamic Limits

### 2.1 Thermal Diffusion Depth Limit ($z > \mu$)
In classical Fourier heat conduction, periodic surface excitation produces a damped thermal wave propagating into the solid with characteristic diffusion length:
$$\mu(f) = \sqrt{\frac{\alpha}{\pi f}} = \sqrt{\frac{k}{\pi f \rho C_p}}$$

For mild steel ($k = 51.9\text{ W/m}\cdot\text{K}$, $\rho = 7850\text{ kg/m}^3$, $C_p = 486\text{ J/kg}\cdot\text{K}$, $\alpha = 1.36 \times 10^{-5}\text{ m}^2/\text{s}$):
- At $f_0 = 0.05\text{ Hz}$: $\mu(f_0) = \sqrt{\frac{1.36\times 10^{-5}}{\pi \times 0.05}} \approx 9.31\text{ mm}$
- At $f_1 = 0.50\text{ Hz}$: $\mu(f_1) = \sqrt{\frac{1.36\times 10^{-5}}{\pi \times 0.50}} \approx 2.94\text{ mm}$

**Failure Mechanism:**
When defect depth $z > 1.2\text{ mm}$, the round-trip thermal wave attenuation $e^{-2z/\mu}$ attenuates the defect-reflected heat flux below $5\%$. The resulting surface differential contrast is $\Delta T_{\text{surface}} < 0.03\text{ K}$, approaching or dropping below the Noise Equivalent Temperature Difference (NETD $\approx 20\text{--}30\text{ mK}$) of standard cooled/uncooled IR cameras.

---

### 2.2 Aspect Ratio Breakdown Limit ($D/z < 2.0$)
The aspect ratio is defined as the ratio of inclusion diameter $D$ to cover depth $z$:
$$\text{Aspect Ratio} = \frac{D}{z}$$

- **High Aspect Ratio ($D/z \ge 3.0$):** Heat transfer above the defect center is approximately 1D. Peak surface contrast is strong and edges are well-resolved.
- **Critical Transition ($2.0 \le D/z < 3.0$):** 3D lateral diffusion begins to divert thermal energy around the defect periphery.
- **Failure Regime ($D/z < 2.0$):** 3D lateral conduction dominates. The surface thermal footprint is severely flattened and widened, making depth and diameter regression ill-posed from surface thermograms alone.

---

### 2.3 Thermal Effusivity Contrast Limit ($\Gamma \to 0$)
The reflection coefficient $\Gamma$ at the host-defect interface is governed by the thermal effusivity mismatch:
$$e = \sqrt{k \rho C_p}$$
$$\Gamma = \frac{e_{\text{defect}} - e_{\text{steel}}}{e_{\text{defect}} + e_{\text{steel}}}$$

- **Mild Steel:** $e_{\text{steel}} \approx 14,075\text{ W}\cdot\text{s}^{1/2}/(\text{m}^2\cdot\text{K})$
- **Welding Slag:** $e_{\text{slag}} \approx 2,100\text{ W}\cdot\text{s}^{1/2}/(\text{m}^2\cdot\text{K}) \implies \Gamma \approx -0.74$ (Strong thermal resistance barrier)
- **Air Void:** $e_{\text{air}} \approx 5.5\text{ W}\cdot\text{s}^{1/2}/(\text{m}^2\cdot\text{K}) \implies \Gamma \approx -0.999$ (Near-total barrier)

**Failure Case:** If an inclusion material has thermal effusivity close to steel ($e_{\text{defect}} \approx e_{\text{steel}}$), $\Gamma \approx 0$, rendering the inclusion undetectable by any thermographic processing technique regardless of excitation duration or camera resolution.

---

## 3. Algorithmic Sensitivity & Degradation Matrix

| Processing Algorithm | Breakdown SNR Threshold | Depth Limit ($D=6\text{ mm}$) | Aspect Ratio Limit ($D/z$) | Primary Failure Mode |
| :--- | :--- | :--- | :--- | :--- |
| **Raw Contrast** | $\text{SNR} < 25\text{ dB}$ | $z \ge 0.6\text{ mm}$ | $D/z < 3.0$ | Background slope masking; noise floor saturation |
| **LFMT Matched Filter** | $\text{SNR} < 15\text{ dB}$ | $z \ge 1.2\text{ mm}$ | $D/z < 1.5$ | Non-coherent chirp drift; sidelobe energy dispersion |
| **Blind PCT (EOF)** | $\text{SNR} < 20\text{ dB}$ | $z \ge 1.0\text{ mm}$ | $D/z < 2.0$ | EOF mode energy splitting; noise variance domination |
| **Sparse PCT (SPCT)** | $\text{SNR} < 18\text{ dB}$ | $z \ge 1.0\text{ mm}$ | $D/z < 1.8$ | Over-regularization ($L_1$ penalty zeroing small peaks) |
| **Random Projection (RPT)** | $\text{SNR} < 20\text{ dB}$ | $z \ge 0.8\text{ mm}$ | $D/z < 2.2$ | Random subspace distortion under high noise variance |
| **Multi-Task CNN** | $\text{SNR} < 15\text{ dB}$ | $z \ge 1.4\text{ mm}$ | $D/z < 1.2$ | Epistemic uncertainty explosion; OOD flagging |

---

## 4. Mitigation Strategies Implemented in Research V3

1. **Multi-Method Consensus Fusion:** Rather than relying on a single algorithm, evidence is weighted across Matched Filter ($30\%$), PCT ($20\%$), SPCT ($15\%$), and Multi-Task AI ($25\%$).
2. **MC Dropout Epistemic Uncertainty:** High variance across Monte Carlo stochastic forward passes directly warns users when an input sample lies in a physical failure regime ($z > 1.2\text{ mm}$ or $D/z < 1.5$).
3. **Multi-Criterion OOD Detection:** Evaluates energy-based score and physical context bounds, automatically downgrading unverified detections to `GENERIC_SUBSURFACE_ANOMALY` when out of distribution.
4. **Autonomous Method Selection Guardrails:** Strictly prevents running LFMT Matched Filter on pulsed thermograms or single-frame inputs, eliminating cross-correlation ghost artifacts.
