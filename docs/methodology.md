# LFMT Methodology & Theoretical Foundation

## 1. Non-Destructive Testing by Active Thermography
Active Infrared Thermography utilizes external thermal excitation to generate transient thermal gradients inside a structural material. When heat diffuses into the specimen, subsurface defects such as welding slag inclusions act as thermal insulation barriers due to their lower thermal conductivity, causing localized heat accumulation on the front surface.

## 2. Linear Frequency-Modulated Thermography (LFMT)
Unlike pulsed thermography (which requires high instantaneous optical peak power) or lock-in thermography (which excites a single frequency at a time, requiring long multi-frequency tests), **LFMT (thermal chirp)** continuously sweeps an excitation frequency $f(t) = f_0 + \beta t$ over a designated bandwidth. This concentrates wideband thermal probing depth information into a single energy-efficient continuous test.

### Thermal Diffusion Length Probing
The thermal penetration depth $\mu$ governed by diffusion length is given by:
$$\mu(f) = \sqrt{\frac{\alpha}{\pi f}}$$
As frequency continuously sweeps from $f_0$ (deep penetration) to $f_1$ (near-surface probing), defects at various depths ($0.2 - 1.0\text{ mm}$) resonate with maximum thermal phase and contrast signatures.

## 3. Signal Processing Algorithms
1. **Pulse Compression / Matched Filtering**: Correlates the temporal temperature history with the excitation chirp reference, compressing energy into a sharp correlation peak that dramatically boosts SNR.
2. **Principal Component Thermography (PCT)**: Decomposes the spatial-temporal matrix $A \in \mathbb{R}^{N_t \times (H \cdot W)}$ using Singular Value Decomposition (SVD), isolating defect signatures into orthogonal Empirical Orthogonal Functions (EOFs).
3. **Sparse PCT (SPCT)**: Imposes $L_1$ regularization ($\alpha$) on the spatial projection basis to enforce sparse localized defect bounding.
4. **Random Projection Technique (RPT)**: Embeds high-dimensional thermal transient curves into low-dimensional subspaces while strictly preserving Euclidean distances according to the Johnson-Lindenstrauss lemma.
