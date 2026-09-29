# LFMT Slag Detection — 5-Minute Viva Demonstration Flow

**Project:** Linear Frequency-Modulated Infrared Thermography (LFMT) for Subsurface Slag Inclusion Detection in Mild Steel  
**Target Audience:** External Examiner / Project Evaluation Committee / Research Guide

---

## Chronological 5-Minute Demonstration Sequence

### ⏱ Minute 1: The Engineering Problem & Motivation
- **Statement:** Slag inclusions formed during steel casting/welding act as stress concentration zones causing catastrophic brittle failure.
- **Limitation of Classic PT:** Conventional Pulse Thermography (PT) suffers from high peak surface temperatures ($>100^\circ\text{C}$) and rapid diffusion attenuation for deep defects ($>0.5\text{ mm}$).
- **The LFMT Solution:** Modulating heat flux as a linear frequency chirp ($0.05 \to 0.50\text{ Hz}$) limits surface heating while concentrating energy across a broad spectral depth range.

---

### ⏱ Minute 2: LFMT Excitation & 3-D Hex8 Specimen Physics
- **Action in LFMTLiveLab:** Navigate to **Tab 2: SIMULATION CONNECTION** and **Tab 3: FEM & 3D MODEL**.
- **Key Physics to Highlight:**
  - Steel plate: AISI 1018 mild steel ($k = 51.9\text{ W/mK}, \rho = 7850\text{ kg/m}^3, C_p = 486\text{ J/kgK}$).
  - Slag inclusion: Silicate slag ($k = 1.20\text{ W/mK}$) — $43\times$ lower conductivity creates strong thermal wave reflection.
  - Hex8 FEM: Unconditionally stable Implicit Backward Euler solver with pre-factorized Cholesky decomposition solving $M \dot{T} + (K + M_{\text{conv}})T = Q(t)$.

---

### ⏱ Minute 3: Real-Time Live Inspection & Thermal Video
- **Action in LFMTLiveLab:** In **Tab 1: LIVE INSPECTION**, select **Demo 2: Standard ($D=8\text{ mm}, z=0.4\text{ mm}, 25\text{ dB SNR}$)** and click **▶ RUN INSPECTION**.
- **Visuals:**
  - Watch live progress lamps cycle across all 8 simulation stages.
  - Scrub thermal video slider: explain how peak thermal contrast occurs around $t \approx 5.5\text{ s}$.
  - Click on the defect center to show the temperature transient vs sound steel baseline in the Point Inspector.

---

### ⏱ Minute 4: 5 Blind Methods & Defect Characterization
- **Action in LFMTLiveLab:** Switch to **Tab 5: 5-METHOD BENCHMARK**.
- **Results Discussion:**
  1. **Raw Contrast:** Shows noisy background ($CNR \approx 2.9$).
  2. **Matched Filter (Pulse Compression):** Compresses energy, maximizing SNR ($CNR \approx 2.55, \text{IoU} \approx 0.68$).
  3. **SVD-PCT:** Second empirical orthogonal function isolates defect mode ($\text{IoU} \approx 0.77, \text{Dice} \approx 0.87$).
  4. **SPCT (Sparse PCA):** Enforces spatial sparsity to suppress background gradients.
  5. **RPT (Random Projection):** Ultra-fast dimension reduction via Gaussian Johnson-Lindenstrauss projection.
- **Quantitative Metrics:** Point to the live summary table showing defect detection, centroid error ($<0.5\text{ mm}$), and estimated diameter.

---

### ⏱ Minute 5: Healthy Control Verification & Connection Architecture
- **Action in LFMTLiveLab:**
  1. Click **"🟢 Healthy Control"**: Show that with 0 defects embedded, all detectors report **False Positive: NO (100% Specificity)**.
  2. Click **"🔍 View Sim Flow"** and **"📊 View 5 Detectors"**: Display the publication connection diagrams.
  3. Click **"⚙️ Open Simulink"**: Show the native 11-subsystem `LFMT_System_Connection.slx` model.
  4. Click **"📦 Export Package"**: Show the 20-artifact bundle generated for report archiving.
- **Closing Conclusion:** LFMT combined with Matched Filtering and PCT achieves reliable, non-destructive, subsurface slag detection in mild steel without ground-truth leakage.
