# LFMT Slag Detection — Final Demonstration & Viva User Guide

**Project:** Linear Frequency-Modulated Infrared Thermography (LFMT) for Subsurface Slag Inclusion Detection in Mild Steel  
**Repository:** `E:\lfmt-slag-detection`  
**MATLAB Root:** `E:\lfmt-slag-detection\matlab`  
**Target Environments:** MATLAB R2026a (or R2020b+), Windows 11 64-bit

---

## 1. Quick-Start Launch Options

### Option A: Interactive MATLAB GUI (One-Click)
In MATLAB Command Window:
```matlab
cd('E:\lfmt-slag-detection\matlab')
LFMTLiveLab;
```
Or double-click `Start_LFMT_LiveLab.bat` from Windows Explorer.

### Option B: Flagship Viva Demonstration Script
In MATLAB Command Window:
```matlab
cd('E:\lfmt-slag-detection\matlab')
run_final_demo;
```
*(Runs the standard $D=8\text{ mm}, z=0.4\text{ mm}, 25\text{ dB SNR}$ case, prints metrics and scientific explanation, and exports all 20 demonstration artifacts into `matlab/results/final_demo/<timestamp>/`).*

### Option C: Run Master Test Suite
```matlab
cd('E:\lfmt-slag-detection\matlab')
res = run_tests();
```
*(Executes all 44 unit and integration tests with 100% green pass).*

---

## 2. Standard Demonstration Presets in LFMTLiveLab

| Preset Name | Specimen Configuration | Noise Model | Typical Outcome | Key Scientific Takeaway |
|---|---|---|---|---|
| **Demo 1: Shallow** | $D = 10.0\text{ mm}, z = 0.20\text{ mm}$ | Clean ($\infty\text{ dB}$) | High SNR, $\text{IoU} > 0.85$, $CNR > 3.0$ | Strong thermal contrast close to surface ($z \ll \mu$). |
| **Demo 2: Standard** | $D = 8.0\text{ mm}, z = 0.40\text{ mm}$ | $25\text{ dB SNR}$ | Reliable detection, $\text{IoU} \approx 0.70-0.85$ | Baseline research benchmark case for weldments. |
| **Demo 3: Deep** | $D = 8.0\text{ mm}, z = 0.80\text{ mm}$ | $25\text{ dB SNR}$ | Detectable via MF & PCT, lower $\Delta T$ | Demonstrates thermal wave diffusive attenuation. |
| **Demo 4: Hard** | $D = 4.0\text{ mm}, z = 1.00\text{ mm}$ | $20\text{ dB SNR}$ | Weak anomaly at detection boundary | Near theoretical limit of thermal diffusion resolution. |
| **Demo 5: Healthy Control** | $D = 0.0\text{ mm}$ (No Inclusion) | Clean / $25\text{ dB}$ | Zero candidates, False Positive: NO | Proves algorithm specificity and 0% false alarms. |

---

## 3. Demonstration Walkthrough Sequence

1. **Geometry & Physical Model (Tab 3: FEM & 3D MODEL):**
   - Show the 3-D AISI 1018 steel plate with embedded cylindrical silicate slag inclusion.
   - Explain the $43\times$ thermal conductivity contrast ($k_{\text{steel}} = 51.9\text{ W/mK}$ vs $k_{\text{slag}} = 1.20\text{ W/mK}$).
2. **Simulation Connection Architecture (Tab 2: SIMULATION CONNECTION):**
   - Click **`🔍 View Sim Flow`** to open the publication pipeline diagram.
   - Click **`📊 View 5 Detectors`** to inspect the 5 blind signal processing suite & segmentation diagram.
   - Click **`⚙️ Open Simulink`** to explore `LFMT_System_Connection.slx`.
3. **Live Inspection & Execution (Tab 1: LIVE INSPECTION):**
   - Select **Demo 2: Standard**, click **`▶ RUN INSPECTION`**.
   - Watch the stage lamps update from `Stage 1: Config` through `Stage 8: Complete`.
   - Scrub the thermal video timeline and click the defect center to show the transient curve vs sound steel.
4. **5 Blind Methods Comparison (Tab 5: 5-METHOD BENCHMARK):**
   - Compare Raw Contrast, Matched Filter, PCT, SPCT, and RPT.
   - Discuss why Matched Filter (Pulse Compression) and SVD-PCT yield superior IoU and CNR.
5. **Healthy Control Test:**
   - Click **`🟢 Healthy Control`**: demonstrate that the app reports **False Positive: NO (100% Specificity)**.
6. **Artifact Export:**
   - Click **`📦 Export Package`** or run `run_final_demo`: inspect the generated 20-file bundle.
