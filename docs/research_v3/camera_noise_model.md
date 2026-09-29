# Infrared Radiometry & Camera Noise Model

**Research V3 Technical Reference**  
**Repository:** `skmdshariff143-ai/lfmt-slag-detection`

---

## 1. Overview of Thermal Sensor Noise

Real infrared focal plane arrays (IR FPAs, e.g. cooled InSb or uncooled microbolometers) exhibit multiple additive, multiplicative, and correlated noise sources. Research V3 incorporates a calibrated radiometric noise model to synthesize realistic virtual thermograms from noise-free FEM surface temperature fields.

---

## 2. Mathematical Formulation

Let $T_{\text{ideal}}(x, y, t)$ be the pure surface temperature field predicted by the 3D FEM heat equation solver. The simulated camera reading $T_{\text{meas}}(x, y, t)$ is modeled as:

$$T_{\text{meas}}(x, y, t) = T_{\text{ideal}}(x, y, t) + n_{\text{temporal}}(x, y, t) + n_{\text{fpn}}(x, y) + n_{\text{drift}}(t) + n_{\text{quant}}(x, y, t)$$

### 2.1. Temporal NETD Noise ($n_{\text{temporal}}$)
Zero-mean Gaussian noise representing thermal photon fluctuations and readout electronics noise, parameterized by Noise Equivalent Temperature Difference ($\text{NETD}$):

$$n_{\text{temporal}}(x, y, t) \sim \mathcal{N}(0, \sigma_{\text{NETD}}^2)$$

- Standard cooled MWIR camera baseline: $\sigma_{\text{NETD}} = 0.020\text{ K}$ ($20\text{ mK}$).
- Uncooled LWIR microbolometer baseline: $\sigma_{\text{NETD}} = 0.050\text{ K}$ ($50\text{ mK}$).

### 2.2. Fixed Pattern Noise ($n_{\text{fpn}}$)
Spatial non-uniformity across detector pixels remaining after non-uniformity correction (NUC), modeled as a spatially correlated 2D Gaussian field with characteristic spatial correlation length $\ell_{\text{corr}} \approx 3\text{--}5\text{ pixels}$:

$$n_{\text{fpn}}(x, y) \sim \mathcal{GP}(0, K_{\text{SE}}(r))$$
$$K_{\text{SE}}(r) = \sigma_{\text{FPN}}^2 \exp\left(-\frac{r^2}{2\ell_{\text{corr}}^2}\right)$$
where default residual non-uniformity is $\sigma_{\text{FPN}} = 0.015\text{ K}$.

### 2.3. Slow Ambient Drift ($n_{\text{drift}}$)
Low-frequency thermal drift caused by lab ambient temperature fluctuations and camera housing warming:

$$n_{\text{drift}}(t) = A_{\text{drift}} \sin(2\pi f_{\text{drift}} t + \phi) + r_{\text{linear}} \cdot t$$
with typical rate $|r_{\text{linear}}| \le 0.005\text{ K/s}$.

### 2.4. Analog-to-Digital Quantization ($n_{\text{quant}}$)
14-bit or 16-bit analog-to-digital conversion with quantization step size $\Delta T_{\text{LSB}} = \frac{T_{\text{max}} - T_{\text{min}}}{2^{B} - 1}$:

$$T_{\text{quantized}} = \text{round}\left(\frac{T}{\Delta T_{\text{LSB}}}\right) \cdot \Delta T_{\text{LSB}}$$

---

## 3. Seed Determinism & Reproducibility Guarantee

In Research V3, camera noise generation strictly adheres to deterministic pseudo-random seeds. For the benchmark evaluation:
- Seeds $s \in \{1001, 1002, \dots, 1010\}$ are used across 10 noise realizations per physical configuration.
- Noise realization arrays produce verified identical SHA256 checksums across repeated test runs.
