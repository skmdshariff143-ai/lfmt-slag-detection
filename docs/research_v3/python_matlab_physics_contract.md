# Python FEM vs. MATLAB FDM Physics & Numerical Discretization Contract

**Project:** Linear Frequency-Modulated Infrared Thermography (LFMT) for Subsurface Slag Detection in Mild Steel  
**Branch:** `scientific-hardening-v3`  
**Date:** 2026-09-22  
**Lead Roles:** Principal Thermal Modelling Researcher, Finite-Element / Finite-Difference Specialist, Reproducibility Auditor

---

## 1. Mathematical Governing Equation

Both the Python FEM backend and the MATLAB FDM backend solve the identical 3-D transient parabolic heat conduction equation for heterogeneous solid media:

$$\rho(\mathbf{x}) C_p(\mathbf{x}) \frac{\partial T(\mathbf{x}, t)}{\partial t} = \nabla \cdot \Big( k(\mathbf{x}) \nabla T(\mathbf{x}, t) \Big) \quad \text{in } \Omega = [0, L_x] \times [0, L_y] \times [0, L_z]$$

where:
- $T(\mathbf{x}, t)$ is the absolute temperature field in Kelvin ($[\text{K}]$).
- $k(\mathbf{x})$ is the spatially varying thermal conductivity ($[\text{W/(m}\cdot\text{K)}]$).
- $\rho(\mathbf{x})$ is the material density ($[\text{kg/m}^3]$).
- $C_p(\mathbf{x})$ is the specific heat capacity ($[\text{J/(kg}\cdot\text{K)}]$).
- $C_v(\mathbf{x}) = \rho(\mathbf{x}) C_p(\mathbf{x})$ is the volumetric heat capacity ($[\text{J/(m}^3\cdot\text{K)}]$).

---

## 2. Spatial Domain & Geometry Conventions

All spatial quantities are discretized in strict SI units ($[\text{m}]$):

| Physical Parameter | Value in mm | Value in SI (m) | Coordinate Axis / Bounds |
| :--- | :--- | :--- | :--- |
| Plate Length ($L_x$) | $100.0\text{ mm}$ | $0.100\text{ m}$ | $x \in [0, L_x]$ |
| Plate Width ($L_y$) | $70.0\text{ mm}$ | $0.070\text{ m}$ | $y \in [0, L_y]$ |
| Plate Thickness ($L_z$) | $2.3\text{ mm}$ | $0.0023\text{ m}$ | $z \in [0, L_z]$ |
| Front / Inspected Face | $z = 0.0\text{ mm}$ | $z = 0.0000\text{ m}$ | Heated and camera-monitored boundary |
| Rear / Back Face | $z = 2.3\text{ mm}$ | $z = 0.0023\text{ m}$ | Rear boundary face |
| Defect Depth ($d$) | Configurable (e.g. $0.4, 0.8\text{ mm}$) | $d \times 10^{-3}\text{ m}$ | Distance from top surface ($z=0$) to top of defect |
| Defect Thickness ($t_{\text{def}}$) | $0.40\text{ mm}$ | $0.00040\text{ m}$ | Defect vertical extent: $z \in [d, d + t_{\text{def}}]$ |
| Defect Center ($x_c, y_c$) | $(50.0, 35.0)\text{ mm}$ | $(0.050, 0.035)\text{ m}$ | Lateral centroid in plate reference frame |
| Defect Diameter ($D$) | $8.0\text{ mm}$ | $0.008\text{ m}$ | Cylinder radius $R = D/2 = 0.004\text{ m}$ |

---

## 3. Heterogeneous Material Properties

| Material Domain | Subdomain Indicator | $k$ [$\text{W/(m}\cdot\text{K)}$] | $\rho$ [$\text{kg/m}^3$] | $C_p$ [$\text{J/(kg}\cdot\text{K)}$] | $C_v = \rho C_p$ [$\text{J/(m}^3\cdot\text{K)}$] |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Mild Steel (AISI 1018)** | Base plate matrix ($\Omega \setminus \Omega_{\text{def}}$) | $51.90$ | $7860.0$ | $486.0$ | $3.81996 \times 10^6$ |
| **Slag Inclusion** | Subsurface defect ($\Omega_{\text{def}}$) | $1.50$ | $2800.0$ | $800.0$ | $2.24000 \times 10^6$ |

---

## 4. LFMT Excitation & Boundary Conditions

### 4.1. LFMT Temporal Heat Flux
$$\beta = \frac{f_1 - f_0}{T_{\text{exc}}}, \quad \phi(t) = 2\pi\left(f_0 t + \frac{1}{2}\beta t^2\right)$$
$$q(t) = q_0 \big(1 + \sin(\phi(t))\big)$$
For baseline benchmark: $f_0 = 0.05\text{ Hz}, f_1 = 0.50\text{ Hz}, T_{\text{exc}} = 10.0\text{ s}, q_0 = 5000.0\text{ W/m}^2$.
- $q_{\text{min}} = 0.0\text{ W/m}^2$
- $q_{\text{mean}} = q_0 = 5000.0\text{ W/m}^2$
- $q_{\text{max}} = 2q_0 = 10000.0\text{ W/m}^2$

### 4.2. Boundary Condition Formulation
- **All 6 External Boundaries ($\Gamma_{\text{all}}$):** Robin convective heat transfer to ambient:
  $$-k(\mathbf{x}) \frac{\partial T}{\partial n} = h_{\text{conv}} (T - T_{\text{amb}})$$
  where $h_{\text{conv}} = 10.0\text{ W/(m}^2\cdot\text{K)}$ and $T_{\text{amb}} = 293.15\text{ K}$ ($20.0^\circ\text{C}$).
- **Front Top Boundary ($\Gamma_{\text{front}}$, $z = 0$):** Convection plus incoming LFMT heat flux:
  $$-k(\mathbf{x}) \left(-\frac{\partial T}{\partial z}\right) = q(t) - h_{\text{conv}} (T - T_{\text{amb}}) \implies k \frac{\partial T}{\partial z} = q(t) - h_{\text{conv}}(T - T_{\text{amb}})$$

---

## 5. Numerical Backend Architectures

| Feature | Python Reference Backend | MATLAB Numerical Backend |
| :--- | :--- | :--- |
| **Scientific Identifier** | `python_fem` | `matlab_fdm` |
| **Numerical Formulation** | 3-D Trilinear Hexahedral Finite Element Method (`scikit-fem` `ElementHex1`) | 3-D Conservative Flux Finite Difference Method (Harmonic mean interface conductivity) |
| **Time Integration** | Implicit Backward Euler: $(M/\Delta t + K + M_{\text{conv}}) u^{n+1} = (M/\Delta t) u^n + q(t^{n+1}) f_{\text{front}} + f_{\text{amb}}$ | Implicit Backward Euler: $(C/\Delta t + L + H) T^{n+1} = (C/\Delta t) T^n + Q^{n+1} + H T_{\text{amb}}$ |
| **Sparse Solver** | `scipy.sparse.linalg.factorized` (SuperLU sparse LU factorization) | MATLAB Sparse Factorization (`decomposition` / sparse Cholesky/LU) |
| **Initial Condition** | $T(\mathbf{x}, 0) = T_{\text{amb}} = 293.15\text{ K}$ | $T(\mathbf{x}, 0) = T_{\text{amb}} = 293.15\text{ K}$ |
| **Camera Output Grid** | Regular $N_x = 40, N_y = 28$ array, shape `[n_frames, 28, 40]` | Regular $N_x = 40, N_y = 28$ array, shape `[n_frames, 28, 40]` |

---

## 6. Strict Terminology & Research Guardrails

1. **No False Nomenclature:** `matlab_fdm` must NEVER be referred to as "FEM", "finite element", "exact", or "ground truth".
2. **Independent Cross-Check:** Both solvers are independent numerical implementations of the same continuum physics. Differences between FDM and FEM arise legitimately from spatial discretization, interface representations, and quadrature.
3. **Zero Parameter Tuning:** Material properties ($k, \rho, C_p$), geometries, and heat flux amplitudes must remain strictly identical across both solvers.
