# Mathematical Equations Reference

## 1. LFMT Chirp Waveform
- Sweep Rate:
  $$\beta = \frac{f_1 - f_0}{T_{exc}} \quad [\mathrm{Hz/s}]$$
- Instantaneous Frequency:
  $$f(t) = f_0 + \beta t \quad [\mathrm{Hz}]$$
- Instantaneous Phase:
  $$\phi(t) = 2\pi \left(f_0 t + \frac{1}{2}\beta t^2\right) \quad [\mathrm{rad}]$$
- Applied Heat Flux:
  $$q(t) = q_0 \cdot [1 + \sin(\phi(t))] \quad \left[\mathrm{W/m^2}\right]$$

## 2. 3D Heterogeneous Transient Heat Conduction
$$\rho(\mathbf{x}) C_p(\mathbf{x}) \frac{\partial T}{\partial t} = \nabla \cdot (k(\mathbf{x}) \nabla T) + Q(\mathbf{x}, t)$$

### Boundary Conditions
- **Heated Surface ($z = 0$):**
  $$-k \left.\frac{\partial T}{\partial z}\right|_{z=0} = q(t) - h_{conv}(T(x,y,0,t) - T_{amb}) - \epsilon \sigma (T^4 - T_{amb}^4)$$
- **Rear Surface ($z = L_z$):**
  $$-k \left.\frac{\partial T}{\partial z}\right|_{z=L_z} = h_{conv}(T(x,y,L_z,t) - T_{amb})$$
- **Lateral Faces:**
  $$-k \nabla T \cdot \mathbf{n} = h_{conv}(T - T_{amb})$$

## 3. Matched Filter (Pulse Compression)
$$R_{xy}(\tau) = \int_{-\infty}^{\infty} T_{xy}^{AC}(t) \cdot s(t + \tau) \, dt = \mathcal{F}^{-1}\{\mathcal{F}\{T_{xy}^{AC}\} \cdot \mathcal{F}^*\{s\}\}$$
$$\text{Peak Correlation Map}(x, y) = \max_\tau |R_{xy}(\tau)|$$
$$\text{Time-of-Flight Delay Map}(x, y) = \arg\max_\tau |R_{xy}(\tau)|$$

## 4. Thermophysical Derived Quantities
- Thermal Diffusivity:
  $$\alpha = \frac{k}{\rho C_p} \quad \left[\mathrm{m^2/s}\right]$$
- Thermal Effusivity:
  $$e = \sqrt{k \rho C_p} \quad \left[\mathrm{W\cdot s^{1/2}/(m^2\cdot K)}\right]$$

## 5. Performance Evaluation Metrics
- **Intersection over Union (IoU):**
  $$\text{IoU} = \frac{|M_{pred} \cap M_{gt}|}{|M_{pred} \cup M_{gt}|}$$
- **Dice Similarity Coefficient:**
  $$\text{Dice} = \frac{2 |M_{pred} \cap M_{gt}|}{|M_{pred}| + |M_{gt}|}$$
- **Localization Error:**
  $$E_{loc} = \sqrt{(x_{pred} - x_{gt})^2 + (y_{pred} - y_{gt})^2} \quad [\mathrm{mm}]$$
- **Contrast-to-Noise Ratio (CNR):**
  $$\text{CNR} = \frac{|\mu_{defect} - \mu_{sound}|}{\sqrt{\sigma_{defect}^2 + \sigma_{sound}^2}}$$
