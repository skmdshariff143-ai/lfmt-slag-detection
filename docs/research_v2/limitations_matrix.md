# Research V2 Limitations Matrix & Scientific Assumptions

This document outlines the numerical, physical, and observational assumptions underlying the LFMT Research V2 simulation and detection framework, their validity bounds, and their expected influence on experimental transferability.

---

## 1. Physics & Numerical Discretization Limitations

| Domain / Component | Assumption / Formulation | Validity Range | Potential Error Source | Mitigation in Research V2 |
| :--- | :--- | :--- | :--- | :--- |
| **Material Homogeneity** | Constant matrix ($k=50\text{ W}/(\text{m}\cdot\text{K})$, $\rho=7850\text{ kg}/\text{m}^3$, $c_p=480\text{ J}/(\text{kg}\cdot\text{K})$) | $T < 350\text{ K}$ ($\Delta T \le 15\text{ K}$) | Temperature-dependent conductivity ($\partial k / \partial T$) | Negligible for low-power LFMT; verified $\Delta T \le 7\text{ K}$. |
| **Defect Geometry** | Canonical cylinders, ellipses, strips, and Fourier-perturbed irregular shapes | Subsurface planar inclusion | Natural slag porosity and fractal jaggedness | Added multi-shape and Fourier perturbed inclusions. |
| **Contact Resistance** | Imperfect thermal boundary ($h_{\text{contact}} \approx 10^3 - 10^5\text{ W}/(\text{m}^2\cdot\text{K})$) | Partial air gap / oxide barrier | Sharp jump conditions vs finite boundary layer | Implemented $h_{\text{contact}}$ boundary conductance in FEM matrix. |
| **Weld / HAZ Microstructure** | Optional central bead ($k_{\text{weld}} = 42\text{ W}/(\text{m}\cdot\text{K})$) | Butt weld geometry | Multi-pass grain orientation gradient | Parametric weld and heat-affected-zone (HAZ) subdomains. |
| **Spatial Discretization** | Graded hexahedral tensor elements ($8-12$ elements across defect diameter) | Cover depth $z \ge 0.1\text{ mm}$ | Under-resolution of sub-millimeter micro-porosity | Adaptive graded tensor meshing ($>30,000$ DOFs). |

---

## 2. Optical & Sensor Radiation Limitations

| Component | Physical Model | Validity Regime | Failure Condition | Implementation in V2 |
| :--- | :--- | :--- | :--- | :--- |
| **Surface Radiance** | Stefan-Boltzmann integration $L = \epsilon \sigma T^4 + (1 - \epsilon)\sigma T_{\text{amb}}^4$ | Long-wave IR ($8-14\ \mu\text{m}$) | Strong external reflection sources | Full Planck / Stefan-Boltzmann radiance inversion. |
| **Optical Blur (PSF)** | Spatial 2D Gaussian point-spread function ($\sigma_{\text{psf}} \approx 0.5 - 1.2\text{ px}$) | Diffraction-limited optics | Severe lens aberration or defocus | Optical PSF convolution (`gaussian_filter`). |
| **Camera Noise (FPA)** | NETD ($\sim 25\text{ mK}$) + FPN ($0.2\%$) + Quantization (14-bit) | Standard uncooled microbolometer / cooled InSb | Extreme sensor thermal drift | Multi-component FPA noise pipeline with measured SNR. |

---

## 3. Algorithmic Bounds & Detection Horizon

| Metric / Aspect | Constraint | Failure Threshold | Impact on Research V2 |
| :--- | :--- | :--- | :--- |
| **Geometric Aspect Ratio ($D / z$)** | 3D lateral diffusion bypass | $D / z < 4.0$ (e.g. $D=4\text{ mm}, z=1.2\text{ mm}$) | Contrast drops below detectable noise floor. |
| **Noise Floor** | SNR $\le 20\text{ dB}$ | False alarms on healthy specimens | RPT and Raw Contrast fail; PCT maintains partial robustness. |
| **Evaluation Severity** | Multi-tier localization grading | Tier A (V1) vs Tier C (IoU $\ge 0.25, E_{\text{loc}} \le r$) | Highlights true physical resolution of pulse-compression methods. |

