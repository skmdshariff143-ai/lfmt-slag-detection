# Physical Laboratory Experimental Validation Protocol for LFMT Slag Detection

## 1. Overview & Objectives
This protocol defines the rigorous laboratory methodology required to validate the numerical predictions of the LFMT Research V2 simulation framework using manufactured mild steel calibration specimens containing synthetic and real slag inclusions.

> [!IMPORTANT]
> This protocol specifies real experimental procedures for physical lab testing. In accordance with strict scientific integrity, all numerical validation reported in Research V2 is identified as computational FEM/FDM cross-validation until physical specimen testing is executed under this protocol.

---

## 2. Test Specimen Fabrication & Microstructural Characterization

### Specimen Matrix & Artificial Flaw Insertion
1. **Parent Material**: Structural mild steel (AISI 1018 / ASTM A36), flat plates dimensions $100.0 \pm 0.1\text{ mm} \times 70.0 \pm 0.1\text{ mm} \times 10.0 \pm 0.1\text{ mm}$.
2. **Defect Types**:
   - **Flat-Bottom Holes (FBH)**: Precision end-milled blind holes from the back face leaving ligament depths $z \in \{0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.5, 1.8\}\text{ mm}$ and diameters $D \in \{4, 6, 8, 10, 12\}\text{ mm}$.
   - **Compacted Slag Inclusions**: Pre-drilled cavities packed with calibrated welding slag powder (silicate/rutile based: $k \approx 1.2\text{ W}/(\text{m}\cdot\text{K})$, $\rho \approx 2800\text{ kg}/\text{m}^3$) and sealed with steel back-plugs under hydraulic compression.
   - **Butt-Welded Plates**: GMAW/SMAW multi-pass V-groove weldments with intentionally induced trapped slag lines along the root and heat-affected zones.
3. **Reference Healthy Specimens**: Pristine baseline steel plates with zero internal cavities.

### Pre-Test Non-Destructive Characterization
- **High-Resolution X-Ray Micro-CT**: 160 kV micro-focus CT scan to map the true 3D volumetric geometry, porosity distribution, and centroid coordinates to $\pm 10\ \mu\text{m}$ accuracy.
- **Surface Emissivity Normalization**: Front surfaces coated with high-emissivity matte black spray paint ($\text{Pyromark 2500}$, calibrated emissivity $\epsilon = 0.95 \pm 0.01$).

---

## 3. Optical LFMT Experimental Apparatus & Instrumentation

### Hardware Components
1. **Infrared Camera**:
   - FLIR / Telops cooled InSb focal plane array ($640 \times 512$ pixels, spectral range $3.0 - 5.0\ \mu\text{m}$, NETD $< 20\text{ mK}$, frame rate $F_s = 50.0\text{ Hz}$).
   - Alternatively: Uncooled microbolometer ($640 \times 480$, $8 - 14\ \mu\text{m}$, NETD $< 35\text{ mK}$, $F_s = 30.0\text{ Hz}$).
2. **Optical Excitation Source**:
   - Twin halogen lamp array ($2 \times 1000\text{ W}$) or high-power diode laser source ($808\text{ nm}, 500\text{ W}$) with beam homogenizer optics.
3. **Chirp Modulation Controller**:
   - Arbitrary waveform function generator driving a solid-state SCR power regulator with feedback photodiode monitoring.
   - Chirp profile: Linear sweep from $f_{\text{start}} = 0.01\text{ Hz}$ to $f_{\text{end}} = 0.50\text{ Hz}$ over $T_{\text{duration}} = 10.0\text{ s}$.
4. **Data Acquisition System**:
   - Radiometric 16-bit streaming software synchronized with excitation trigger pulse ($t_0$ sync jitter $< 1\text{ ms}$).

---

## 4. Testing Procedure & Acquisition Protocol

1. **Ambient Thermal Stabilization**: Mount specimen in insulated non-reflective test enclosure; allow specimen and camera core temperature to stabilize ($\Delta T_{\text{drift}} < 0.01\text{ K}/\text{min}$).
2. **Pre-Chirp Baseline Acquisition**: Record 2.0 s (100 frames) of quiescent baseline thermal background.
3. **Active LFMT Excitation**: Trigger chirp excitation for $10.0\text{ s}$ duration while logging full radiometric frame sequence.
4. **Post-Excitation Cool-Down**: Continue acquisition for $15.0\text{ s}$ of thermal decay to capture deep inclusion diffusion return.
5. **Data Export**: Save raw radiometric temperature sequences in 16-bit TIFF / NPY format with complete metadata headers.

---

## 5. Quantitative Validation & Acceptance Criteria

Experimental thermograms are processed using the `lfmt.io_experimental.ExperimentalDataLoader` and evaluated against simulation results using:
1. **Thermal Transients Comparison**: RMSE between simulated surface temperature $T_{\text{FEM}}(t)$ and measured $T_{\text{exp}}(t)$ at sound and defect regions ($\text{RMSE} < 0.25\text{ K}$ target).
2. **Phase & Contrast Verification**: Comparison of matched-filter cross-correlation peak time $\tau_{\text{peak}}$ and PCT component profiles.
3. **Detection & Sizing Benchmark**:
   - Tier B Sizing: $\text{IoU} \ge 0.10$ for $D \ge 6\text{ mm}, z \le 0.8\text{ mm}$.
   - Localization Error: $E_{\text{loc}} \le 1.5\text{ mm}$ for detected inclusions.

