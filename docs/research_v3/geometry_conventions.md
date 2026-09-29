# Geometry & Coordinate System Conventions

**Research V3 Technical Reference**  
**Repository:** `skmdshariff143-ai/lfmt-slag-detection`

---

## 1. Global Coordinate System

The 3-D workpiece geometry conforms to a Cartesian coordinate system $(x, y, z)$ defined as follows:

- **$x$-axis (Length):** $[0, L_x]$, along the longitudinal dimension of the plate (default $L_x = 100.0\text{ mm}$).
- **$y$-axis (Width):** $[0, L_y]$, along the transverse dimension of the plate (default $L_y = 70.0\text{ mm}$).
- **$z$-axis (Depth / Thickness):** $[0, L_z]$, oriented into the plate depth:
  - $z = 0$: **Front (Inspected / Excited) Surface**, illuminated by the optical chirp heat flux and observed by the infrared camera.
  - $z = L_z$: **Back (Rear) Surface**, adiabatic or convective boundary.

```
       +---------------------------------------+
      /|               Top Surface (z=0)       |
     / |       [ Optical Excitation + Camera ] |
    +--+---------------------------------------+
    |  |                                       |
    |  |        z (Depth into thickness)       |
    |  |        ?                              |
    |  +---------------------------------------+
    | /                Bottom Surface (z=L_z)  /
    +-----------------------------------------+
```

---

## 2. Inclusion / Defect Depth Convention

> [!IMPORTANT]
> **Canonical Depth Definition:**
> Defect depth $d$ is strictly defined as the distance from the **front surface ($z=0$) to the top surface of the inclusion** ($z = z_{\text{top}}$).
> 
> $$d_{\text{top}} = z_{\text{top}} = d$$
> $$z_{\text{bottom}} = z_{\text{top}} + t_{\text{defect}} = d + t$$

- For a plate of thickness $L_z = 2.3\text{ mm}$, an inclusion with depth $d = 0.6\text{ mm}$ and thickness $t = 0.5\text{ mm}$ occupies the depth interval $z \in [0.6, 1.1]\text{ mm}$.
- The **cover thickness** is exactly $d_{\text{cover}} = d = 0.6\text{ mm}$.
- The remaining ligament to the back wall is $L_z - (d + t) = 2.3 - 1.1 = 1.2\text{ mm}$.

---

## 3. Inclusion Shapes and In-Plane Parameterizations

Inclusions are parameterized in the $(x, y)$ plane relative to center coordinate $(c_x, c_y)$:

1. **Cylindrical Disk (`cylinder`):**
   $$\sqrt{(x - c_x)^2 + (y - c_y)^2} \le \frac{D}{2}$$
   where $D$ is the inclusion diameter.

2. **Elliptical Inclusion (`ellipse` / `ellipsoid`):**
   $$\left(\frac{x'}{a}\right)^2 + \left(\frac{y'}{b}\right)^2 \le 1$$
   where $a, b$ are semi-major and semi-minor axes, rotated by in-plane orientation angle $\theta$:
   $$x' = (x - c_x)\cos\theta + (y - c_y)\sin\theta$$
   $$y' = -(x - c_x)\sin\theta + (y - c_y)\cos\theta$$

3. **Strip / Slag Line Defect (`strip`):**
   $$|x'| \le a \quad \text{and} \quad |y'| \le b$$

4. **Irregular Multi-Lobed Inclusion (`irregular`):**
   $$r(\phi) \le R_0 \left[1 + 0.20\cos(2\phi) + 0.15\sin(3\phi)\right]$$
   where $\phi = \text{atan2}(y - c_y, x - c_x)$ and $R_0 = D/2$.

5. **Multi-Inclusion Cluster (`multi_inclusion`):**
   Union of two adjacent ellipsoidal/cylindrical inclusions with inter-defect center-to-center separation $s = 2.5 R_0$.

---

## 4. Multi-Zone Weld & HAZ Modeling

When weld modeling is enabled (`weld.enabled = true`):
- **Weld Bead Domain:** $|x - x_{\text{weld}}| \le \frac{w_{\text{weld}}}{2}$
- **Heat Affected Zone (HAZ):** $\frac{w_{\text{weld}}}{2} < |x - x_{\text{weld}}| \le \frac{w_{\text{weld}}}{2} + w_{\text{haz}}$
- **Base Metal:** Everywhere else in $[0, L_x] \times [0, L_y] \times [0, L_z]$.
