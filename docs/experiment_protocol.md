# LFMT Subsurface Slag Detection: Formal Scientific Experiment Protocol

**Document Version**: 1.0  
**Status**: Frozen & Pre-registered  
**Primary Forward Solver**: 3D Finite Element Method (`scikit-fem` hexahedral implicit Euler)  
**Specimen Material**: Mild Steel (AISI 1018, $k=51.9\text{ W/(m}\cdot\text{K)}$, $\rho=7850\text{ kg/m}^3$, $C_p=486\text{ J/(kg}\cdot\text{K)}$)  
**Inclusion Material**: Silicate Welding Slag ($k=1.20\text{ W/(m}\cdot\text{K)}$, $\rho=2800\text{ kg/m}^3$, $C_p=850\text{ J/(kg}\cdot\text{K)}$)  

---

## 1. Objectives & Scope
This protocol establishes the rigorous, blind, and reproducible experimental procedure for assessing **Linear Frequency-Modulated Thermography (LFMT)** combined with five thermographic signal processing algorithms (**Raw Contrast**, **Matched Filter / Pulse Compression**, **Principal Component Thermography (PCT)**, **Sparse PCT (SPCT)**, and **Random Projection Technique (RPT)**) to detect, localize, and size subsurface welding slag inclusions in mild steel plates.

---

## 2. Controlled Geometry Grid (25 Physical Cases + Healthy Controls)

The controlled parameter space consists of 25 distinct defect geometries plus a healthy reference plate:

- **Defect Diameters ($D$)**: $4.0\text{ mm}, 6.0\text{ mm}, 8.0\text{ mm}, 10.0\text{ mm}, 12.0\text{ mm}$
- **Defect Depths ($z$)**: $0.2\text{ mm}, 0.4\text{ mm}, 0.6\text{ mm}, 0.8\text{ mm}, 1.0\text{ mm}$
- **Defect Thickness**: Fixed at $0.5\text{ mm}$
- **Defect Location**: Centered at $(x_c, y_c) = (50.0\text{ mm}, 35.0\text{ mm})$ on a $100.0 \times 70.0 \times 2.3\text{ mm}$ plate.
- **Healthy Control Case**: Plate of identical dimensions with 0 inclusions ($D = 0\text{ mm}$).

---

## 3. Forward Simulation Configuration (Deterministic FEM)

To ensure high numerical precision while maintaining computational feasibility:
- **Solver**: 3D Finite Element Method with trilinear 8-node hexahedra (`MeshHex`, `ElementHex1`).
- **Spatial Resolution**: $\Delta x = \Delta y = 1.0\text{ mm}$, $\Delta z = 0.23\text{ mm}$ ($101 \times 71 \times 11$ nodes = 78,881 DOFs).
- **Time Stepping**: Implicit Euler ($\Delta t = 0.02\text{ s}$, $T_{\mathrm{total}} = 10.0\text{ s}$, 501 time steps).
- **Excitation**: LFMT linear chirp $f_0 = 0.05\text{ Hz} \to f_1 = 0.50\text{ Hz}$, $q_0 = 5000\text{ W/m}^2$, $T_{\mathrm{exc}} = 10.0\text{ s}$.
- **Boundary Conditions**: Top Robin flux/convection ($-k \partial_z T = q(t) - h_{\mathrm{conv}}(T - T_{\mathrm{amb}})$), rear/side convection ($h_{\mathrm{conv}} = 10.0\text{ W/(m}^2\cdot\text{K)}$).
- **Ambient Temperature**: $T_{\mathrm{amb}} = 293.15\text{ K} = 20.00^\circ\text{C}$.

---

## 4. Virtual Camera & Noise Replicates Protocol

1. **Virtual IR Camera**: Captures surface temperature $T(x,y,0,t)$ at spatial grid $64 \times 64$ with sampling frequency $f_s = 25\text{ Hz}$ ($N_t = 250$ frames).
2. **Deterministic Replicates Strategy**:
   - Clean thermograms are simulated **once** per physical geometry and cached.
   - For noisy evaluations, 3 Signal-to-Noise Ratios are tested: $\text{SNR} = 30\text{ dB}, 25\text{ dB}, 20\text{ dB}$.
   - **Random Seeds (10 independent realizations)**:
     `[1001, 1002, 1003, 1004, 1005, 1006, 1007, 1008, 1009, 1010]`
   - Total runs per physical geometry: $1\text{ (clean)} + 3 \times 10\text{ (noisy)} = 31\text{ conditions}$.
   - Across 25 defect geometries + 1 healthy control = **26 physical cases $\times$ 31 conditions = 806 processing evaluations**.

---

## 5. Thermographic Signal Processing (Blind Pipeline)

> [!IMPORTANT]
> **Strict Anti-Leakage Protocol**:
> Ground truth masks and defect coordinates are strictly withheld from all 5 signal processing algorithms.

1. **Raw Thermal Contrast**:
   - Computes spatial variance across all frames to find peak contrast frame $t_{\mathrm{peak}}$.
   - Subtracts trimmed spatial mean baseline.
2. **Matched Filter / Pulse Compression**:
   - Computes temporal FFT cross-correlation against the zero-mean reference AC excitation chirp $q_{\mathrm{ref}}(t)$.
   - Peak magnitude map: $S_{\mathrm{MF}}(x,y) = \max_\tau |R_{xy}(\tau)|$.
3. **Principal Component Thermography (PCT)**:
   - SVD on mean-centered temporal data with $K = 6$ components.
   - **Blind Component Selection**: Component maximizing absolute excess spatial kurtosis $\kappa = |\frac{\mu_4}{\sigma^4} - 3|$.
   - **Blind Polarity Correction**: Sign aligned with positive spatial skewness ($\gamma_1 > 0$).
4. **Sparse PCT (SPCT)**:
   - $L_1$-regularized Sparse PCA ($\alpha = 0.05$, coordinate descent solver).
   - **Blind Component Selection**: Component with highest peak-to-background anomaly score $\max(|S|) / \sigma_S$.
   - **Blind Polarity Correction**: Positive spatial skewness alignment.
5. **Random Projection Technique (RPT)**:
   - Gaussian random projection into $K = 6$ temporal subspace.
   - **Blind Component Selection**: Component with highest dynamic range $\text{ptp}(S)$.
   - **Blind Polarity Correction**: Positive spatial skewness alignment.

---

## 6. Segmentation & Defect Detection

1. **Min-Max Normalization**: Score map $S(x,y) \to [0, 1]$.
2. **Thresholding**: Global adaptive Otsu binarization.
3. **Morphology**: 8-connectivity binary opening followed by binary closing.
4. **Connected Components**: Isolation of 8-connected components. The candidate defect is the largest component with area $\ge 3\text{ pixels}$.
5. **Centroid & Sizing**: Center of mass $(c_x, c_y)$ converted to physical coordinates $(\mathrm{mm})$, equivalent diameter $D_{\mathrm{eq}} = 2 \sqrt{A / \pi}$.

---

## 7. Formal Definition of Detection Success

A run is classified as a **Successful Detection** ($\text{Success} = \text{True}$) if and only if **all three** of the following conditions are simultaneously satisfied:

1. **Defect Isolated**: The segmentation pipeline isolates a candidate cluster with area $A \ge 3\text{ pixels}$ (`is_detected == True`).
2. **Spatial Overlap**: The predicted binary mask intersects the true defect region ($\mathrm{IoU} > 0.0$ and $\mathrm{Dice} > 0.0$).
3. **Centroid Localization Tolerance**: The Euclidean distance between estimated centroid and true defect centroid satisfies:
   $$E_{\mathrm{loc}} = \sqrt{(x_{\mathrm{pred}} - x_{\mathrm{true}})^2 + (y_{\mathrm{pred}} - y_{\mathrm{true}})^2} \le \max\left(\frac{D_{\mathrm{true}}}{2}, 5.0\text{ mm}\right)$$

For healthy control specimens ($D_{\mathrm{true}} = 0\text{ mm}$), any positive detection is recorded as a **False Positive (False Alarm)**.

---

## 8. Definition of Maximum Detectable Depth ($z_{\mathrm{max}}$)

For each defect diameter $D$, processing method $M$, and noise condition $\mathrm{SNR}$, the **Maximum Detectable Depth** $z_{\mathrm{max}}$ is defined as the deepest physical depth $z \in \{0.2, 0.4, 0.6, 0.8, 1.0\}\text{ mm}$ at which the **Detection Success Rate $\ge 80\%$** (i.e. at least 8 out of 10 noisy realizations successfully detected).

---

## 9. Parameter Sensitivity Protocol

On the benchmark case ($D = 8.0\text{ mm}$, $z = 0.4\text{ mm}$), one parameter is varied at a time under clean conditions:
1. **Excitation Heat Flux ($q_0$)**: $-10\%, 0\%, +10\%$ ($4500, 5000, 5500\text{ W/m}^2$)
2. **Slag Thermal Conductivity ($k_{\mathrm{slag}}$)**: $-10\%, 0\%, +10\%$ ($1.08, 1.20, 1.32\text{ W/(m}\cdot\text{K)}$)
3. **Convection Coefficient ($h_{\mathrm{conv}}$)**: $-20\%, 0\%, +20\%$ ($8.0, 10.0, 12.0\text{ W/(m}^2\cdot\text{K)}$)
4. **Slag Specific Heat ($C_{p,\mathrm{slag}}$)**: $-10\%, 0\%, +10\%$ ($765, 850, 935\text{ J/(kg}\cdot\text{K)}$)
