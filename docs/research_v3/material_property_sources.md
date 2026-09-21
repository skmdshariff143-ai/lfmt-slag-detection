# Thermophysical Material Properties & Literature Provenance

**Research V3 Technical Reference**  
**Repository:** `skmdshariff143-ai/lfmt-slag-detection`

---

## 1. Matrix & Inclusion Thermophysical Properties

The numerical models and physics feature extraction modules use thermophysical property values substantiated by peer-reviewed metallurgical and thermophysical literature:

| Material | Density $\rho$ ($\text{kg/m}^3$) | Specific Heat $C_p$ ($\text{J/(kg}\cdot\text{K)}$) | Thermal Conductivity $k$ ($\text{W/(m}\cdot\text{K)}$) | Thermal Diffusivity $\alpha$ ($\text{m}^2/\text{s}$) | Thermal Effusivity $e$ ($\text{W}\cdot\text{s}^{1/2}/(\text{m}^2\cdot\text{K})$) |
|:---|:---:|:---:|:---:|:---:|:---:|
| **AISI 1018 Mild Steel** | $7850$ | $486$ | $51.9$ | $1.36 \times 10^{-5}$ | $14,083$ |
| **Welding Slag Inclusion ($\text{SiO}_2\text{--}\text{CaO}\text{--}\text{FeO}$)** | $2800$ | $800$ | $1.20$ | $5.36 \times 10^{-7}$ | $1,639$ |
| **Weld Metal (ER70S-6)** | $7850$ | $490$ | $48.0$ | $1.25 \times 10^{-5}$ | $13,595$ |
| **Heat Affected Zone (HAZ)** | $7850$ | $500$ | $45.0$ | $1.15 \times 10^{-5}$ | $13,295$ |
| **Air Void / Delamination** | $1.20$ | $1005$ | $0.026$ | $2.16 \times 10^{-5}$ | $5.60$ |

---

## 2. Thermophysical Contrast Metrics

### 2.1. Thermal Diffusivity Ratio
$$\frac{\alpha_{\text{slag}}}{\alpha_{\text{steel}}} = \frac{5.36 \times 10^{-7}}{1.36 \times 10^{-5}} \approx 0.0394 \quad (3.9\%)$$
Slag conducts heat $\sim 25\times$ more slowly than the surrounding steel, acting as a strong internal thermal resistor that impedes downward diffusion into the plate during optical excitation.

### 2.2. Thermal Effusivity Contrast ($R_{\text{eff}}$)
$$R_{\text{eff}} = \frac{e_{\text{steel}} - e_{\text{slag}}}{e_{\text{steel}} + e_{\text{slag}}} = \frac{14,083 - 1,639}{14,083 + 1,639} = \frac{12,444}{15,722} \approx +0.791$$
The large positive reflection coefficient ($+0.79$) confirms strong thermal wave reflection at the steel-slag interface back towards the front surface, producing positive surface temperature elevation $\Delta T > 0$.

---

## 3. Literature References

1. **Incropera, F. P., & DeWitt, D. P.** (2007). *Fundamentals of Heat and Mass Transfer* (6th ed.). John Wiley & Sons. (Thermophysical properties of structural steels).
2. **Mills, K. C.** (2002). *Recommended Values of Thermophysical Properties for Selected Commercial Alloys*. Woodhead Publishing / NPL.
3. **Maldague, X. P. V.** (2001). *Theory and Practice of Infrared Technology for Nondestructive Testing*. John Wiley & Sons.
4. **Mulaveesala, R., & Tuli, S.** (2005). "Theory of localized thermal wave imaging for nondestructive characterization of materials." *NDT & E International*, 38(7), 570-575.
