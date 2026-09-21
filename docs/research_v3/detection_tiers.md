# Defect Detectability Tiers & Classification Matrix

**Research V3 Technical Reference**  
**Repository:** `skmdshariff143-ai/lfmt-slag-detection`

---

## 1. Physical Aspect Ratio & Detectability Metric

In transient thermography, detectability of a subsurface flaw is primarily governed by the dimensionless aspect ratio:

$$\Gamma = \frac{D}{d}$$

where $D$ is the inclusion diameter (or characteristic transverse dimension) and $d$ is the cover depth to the defect top surface. Secondary factors include the thermal effusivity ratio $e_{\text{slag}} / e_{\text{steel}} \approx 0.17$ and the modulation frequency bandwidth $[f_0, f_1]$.

---

## 2. Standard Detectability Tiers

Research V3 categorizes all test cases into four rigorous detection tiers based on physics limits and SNR:

| Tier | Aspect Ratio ($\Gamma = D/d$) | Depth Regime | SNR Regime | Expected Pipeline Response |
|:---|:---:|:---|:---:|:---|
| **Tier A (High Detectability)** | $\Gamma \ge 4.0$ | Shallow ($d \le 0.6\text{ mm}$) | $\text{SNR} > 15\text{ dB}$ | Unambiguous detection across all temporal methods (PCT, SPCT, RPT, Matched Filter). Clear boundary segmentation with $\text{IoU} > 0.75$. |
| **Tier B (Moderate Detectability)** | $2.0 \le \Gamma < 4.0$ | Intermediate ($0.6 < d \le 1.2\text{ mm}$) | $6\text{ dB} \le \text{SNR} \le 15\text{ dB}$ | High detection rate with Matched Filter and Blind PCT. Low contrast may challenge simple thresholding; consensus fusion resolves ambiguity. |
| **Tier C (Marginal / Threshold)** | $1.0 \le \Gamma < 2.0$ | Deep / Small ($1.2 < d \le 1.8\text{ mm}$) | $0\text{ dB} \le \text{SNR} < 6\text{ dB}$ | Lateral heat diffusion significantly attenuates surface footprint. Requires multi-task deep learning and SPCT sparse decomposition. |
| **Tier D (Physical Sub-Resolution / Beyond Limit)** | $\Gamma < 1.0$ | Very Deep ($d > 1.8\text{ mm}$) or Micro ($D < 1\text{ mm}$) | $\text{SNR} < 0\text{ dB}$ | Fundamental physics detection limit for standard LFMT parameters in $2.3\text{ mm}$ steel. Pipeline reports High Uncertainty / Below Detection Threshold. |

---

## 3. Automated Diagnostic Triage Decision Logic

```
                    INPUT THERMAL DATA
                            ¦
              Compute Signal-to-Noise Ratio (SNR)
              & Aspect Ratio Prior (if available)
                            ¦
          +-----------------------------------+
          ¦                                   ¦
      SNR = 6 dB                          SNR < 6 dB
          ¦                                   ¦
    [Tier A / B]                        [Tier C / D]
          ¦                                   ¦
  Full Confidence                     Uncertainty Estimator
  Multi-Method Consensus              MC Dropout Variance High
  Export Defect Bounding Box          Flag "Marginal / Below Limit"
```
