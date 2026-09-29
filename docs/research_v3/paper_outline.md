# IEEE / Scopus Publication Manuscript Outline

**Working Title:**
*Simulation-First Autonomous Thermographic Non-Destructive Testing for Subsurface Defect Characterization in Mild Steel: 3D Finite-Element Modeling, Pulse Compression, and Physics-Informed Multi-Task Consensus*

**Target Venues:**
1. **Conference:** *IEEE International Ultrasonics / Instrumentation and Measurement / QIRT Conference*
2. **Journal Extension:** *IEEE Transactions on Instrumentation and Measurement (TIM)* / *NDT & E International*

---

## Abstract Structure
- **Context & Motivation:** Critical role of mild steel weldment integrity in structural engineering; limitations of radiography (radiation hazards) and conventional ultrasonic testing (contact coupling constraints).
- **Proposed Framework:** Autonomous simulation-first infrared thermography platform combining 3D FEM heat diffusion modeling, phase-delay LFMT chirp matched filtering, blind Principal Component Thermography (PCT), Sparse PCT (SPCT), and Physics-Informed Multi-Task Deep Learning with Monte Carlo Dropout uncertainty.
- **Benchmark Findings (Category A):** Comprehensive numerical benchmark across 4,030 evaluations demonstrates matched filter pulse compression achieves $+8.4\text{ dB}$ SNR improvement over raw contrast, resolving slag inclusions down to $z = 1.0\text{ mm}$ ($D=6\text{ mm}$, $D/z = 6.0$) under $20\text{ dB}$ AWGN.
- **Transfer Study (Category B):** Successful zero-shot cross-modality ingestion and blind feature isolation on external measured flash thermography (Hong Kong PolyU mild steel benchmark plate with 11 flat-bottom holes).
- **Reproducibility & Open Science:** 100% audited open-source implementation with interactive Next.js web portal, FastAPI REST engine, and CI automated test verification.

---

## 1. Introduction
- 1.1 Non-Destructive Testing (NDT) in steel fabrication and weldment inspection.
- 1.2 Thermal wave imaging fundamentals: Pulsed Thermography (PT) vs. Lock-in Thermography (LT) vs. Linear Frequency-Modulated Thermography (LFMT).
- 1.3 Challenges in subsurface slag inclusion detection: low thermal effusivity contrast, 3D lateral diffusion blurring, and depth attenuation.
- 1.4 Research gaps in automated multi-algorithm consensus, blind component selection, and out-of-distribution uncertainty quantification.
- 1.5 Contributions and clear tripartite provenance taxonomy (Categories A, B, C).

---

## 2. Mathematical Modeling & Numerical Simulation (Category A)
- 2.1 3D Transient Heat Conduction Equation with Robin boundary conditions:
  $$\rho C_p \frac{\partial T}{\partial t} = \nabla \cdot (k \nabla T) + Q_{\text{source}}$$
  $$-k \frac{\partial T}{\partial n}\Bigg|_{\Gamma_{\text{top}}} = q_{\text{chirp}}(t) - h(T - T_{\text{amb}}) - \epsilon \sigma (T^4 - T_{\text{amb}}^4)$$
- 2.2 LFMT Chirp Excitation Waveform:
  $$q_{\text{chirp}}(t) = q_0 \left[1 + \sin\left(2\pi \left(f_0 t + \frac{f_1 - f_0}{2T_{\text{dur}}} t^2\right)\right)\right]$$
- 2.3 3D Finite Element Discretization and Implicit Euler Time Stepping.
- 2.4 Virtual Infrared Radiometer & NETD Gaussian Noise Modeling ($15\text{--}35\text{ dB}$ SNR).

---

## 3. Signal Processing & Feature Extraction
- 3.1 Vectorized Matched Filtering & Pulse Compression:
  $$R(\tau, x, y) = \int T_{\text{AC}}(t, x, y) s_{\text{ref}}(t - \tau) dt$$
- 3.2 Blind Principal Component Thermography (PCT) via SVD & Maximum Kurtosis Selection.
- 3.3 Sparse Principal Component Thermography (SPCT) with $L_1$ Elastic Regularization.
- 3.4 Random Projection Technique (RPT) with Johnson-Lindenstrauss Subspace Embedding.
- 3.5 Spatio-Temporal Physical Feature Extraction (14-element feature vector).

---

## 4. Physics-Informed Multi-Task AI & Uncertainty Quantification
- 4.1 Architecture: Shared Convolutional Encoder + MLP Physics Injection ($[\alpha, e, f_0, f_1, \text{fps}, \dots]$).
- 4.2 Multi-Task Heads: Defect Classification, U-Net Segmentation Decoder, Depth Regressor, Diameter Regressor, Centroid Localization.
- 4.3 Epistemic Uncertainty Estimation via Monte Carlo Dropout (30 stochastic forward passes):
  $$\sigma^2_{\text{epistemic}} = \frac{1}{T}\sum_{t=1}^T (\hat{y}_t - \bar{y})^2$$
- 4.4 Energy-Based Out-of-Distribution (OOD) Detection.
- 4.5 Multi-Method Agreement & Consensus Fusion Engine.

---

## 5. Experimental Transfer Demonstration (Category B)
- 5.1 The Hong Kong PolyU Mild Steel Optical Flash Thermography Dataset ($150\times 150\times 10\text{ mm}$, 11 FBHs).
- 5.2 Universal Ingestion & Autonomous Incompatibility Guarding (disabling LFMT Matched Filter for non-LFMT flash excitation).
- 5.3 Blind Spatial and EOF Defect Segmentation Results.
- 5.4 Comparison between Synthetic 3D FEM Profiles and Measured Camera Thermograms.

---

## 6. Results & Discussion
- 6.1 Systematic LFMT Slag Benchmark Results (4,030 evaluations across $D \in [4, 12]\text{ mm}$, $z \in [0.2, 1.0]\text{ mm}$, $\text{SNR} \in [20, 35]\text{ dB}$).
- 6.2 Depth Sensitivity Curves and Aspect Ratio Limits ($D/z \ge 2.0$).
- 6.3 False Positive Rejection on Sound Mild Steel Control Specimens ($100\%$ specificity).
- 6.4 Computational Runtime and Memory Profile across all 5 scientific algorithms.

---

## 7. Threats to Validity & Honest Scientific Limits
- 7.1 Separation between numerical simulation and physical laboratory experiments (Category C).
- 7.2 Surface emissivity variations, non-uniform heating distribution, and ambient reflections.
- 7.3 High-depth attenuation threshold ($z > 1.2\text{ mm}$) and spatial resolution limits.

---

## 8. Conclusion & Future Roadmap
- 8.1 Summary of key findings and algorithmic milestones.
- 8.2 Roadmap toward Category C physical LFMT experimentation with laser excitation and calibrated microbolometer radiometry.
- 8.3 Data availability, reproducible code repository, and interactive web portal.

---

## References (Key Foundational Citations)
1. Maldague, X. *Theory and Practice of Infrared Technology for Nondestructive Testing*, Wiley, 2001.
2. Rajic, N. "Principal component thermography for flaw contrast enhancement in constrained thermal data," *Composite Structures*, 2002.
3. Mulaveesala, R., & Tuli, S. "Theory of matched filter for thermal wave imaging," *Insight*, 2006.
4. Almond, D. P., & Pickering, S. G. "An analytical study of the thermal wave imaging of flaws," *NDT & E International*, 2012.
5. Gal, Y., & Ghahramani, Z. "Dropout as a Bayesian Approximation: Representing Model Uncertainty in Deep Learning," *ICML*, 2016.
