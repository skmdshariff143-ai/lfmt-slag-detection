# LFMT Slag Detection — Scientific Assumptions & Limitations

**Document Version:** 1.0  
**Project:** Linear Frequency-Modulated Infrared Thermography (LFMT) for Subsurface Slag Inclusion Detection in Mild Steel  
**Repository:** `E:\lfmt-slag-detection`

---

## 1. Physical Modeling Assumptions

1. **Material Homogeneity & Isotropism:**
   - AISI 1018 mild steel is modeled as an isotropic, homogeneous continuum with temperature-independent thermal properties ($k = 51.9\text{ W/mK}, \rho = 7850\text{ kg/m}^3, C_p = 486\text{ J/kgK}$).
   - Microstructural grain boundaries, phase transformations, and temperature-dependent non-linearities are neglected over the small temperature rise range ($\Delta T < 10\text{ K}$).

2. **Inclusion Morphology:**
   - Slag inclusions are modeled as idealized circular cylinders embedded at depth $z$. In real cast/weld specimens, slag inclusions exhibit irregular geometric shapes, surface roughness, and porosity.

3. **Thermal Contact Resistance:**
   - Perfect thermal contact is assumed across the steel-slag interface (continuity of temperature and normal heat flux: $k_{\text{steel}} \partial T_1/\partial n = k_{\text{slag}} \partial T_2/\partial n$).
   - Interfacial micro-gaps or oxide films would introduce contact resistance $R_{\text{th}}$, which would further decrease effective heat transfer and amplify thermal contrast.

4. **Surface Emissivity & Uniformity:**
   - Specimen surface emissivity is assumed uniform ($\epsilon \approx 0.95$ typical of matte black paint). Variations in surface roughness or spatial emissivity gradients are modeled as additive Gaussian noise in the sensor stage.

---

## 2. 100% Virtual Simulation Framework

> [!IMPORTANT]
> The LFMT project is **100% COMPUTATIONAL SIMULATION BASED**. All quantitative results are derived from the validated 3-D Hex8 Finite Element Method (FEM) transient thermal solver, decoupled virtual IR camera model, and blind thermographic signal processing algorithms. No physical hardware components or experimental acquisitions are involved.

The virtual simulation pipeline models:
1. Discretized AISI 1018 mild steel plate with cylindrical slag inclusion using Hex8 finite elements.
2. Synthesized linear frequency-modulated optical heat flux boundary conditions ($q_0 = 5000\text{ W/m}^2$, $f = 0.05 \to 0.50\text{ Hz}$).
3. Decoupled virtual radiometric IR camera sensor ($64 \times 64$ spatial grid @ $25\text{ fps}$) with calibrated NETD Gaussian noise.
4. Five parallel blind signal processing methods (Raw Contrast, Matched Filter, SVD-PCT, SPCT, RPT).
