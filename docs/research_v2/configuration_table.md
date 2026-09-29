# Research V2 Configuration Architecture & Schema Reference

The Research V2 framework is configured using YAML schemas parsed into strongly-typed dataclasses in `src/lfmt/config.py`.

---

## 1. Complete Configuration Reference

| Section | Parameter | Type | Default Value | Physical Units | Description / Purpose |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`geometry.plate`** | `length_mm` | `float` | `100.0` | mm | Specimen plate physical length ($X$) |
| | `width_mm` | `float` | `70.0` | mm | Specimen plate physical width ($Y$) |
| | `thickness_mm` | `float` | `10.0` | mm | Specimen plate physical thickness ($Z$) |
| **`geometry.inclusion`** | `shape` | `str` | `"cylinder"` | - | Inclusion geometry (`cylinder`, `ellipse`, `strip`, `irregular`) |
| | `diameter_mm` | `float` | `8.0` | mm | Primary diameter (or major axis) |
| | `depth_mm` | `float` | `0.4` | mm | Ligament cover depth from heated front face |
| | `thickness_mm` | `float` | `1.0` | mm | Inclusion layer thickness along $Z$ |
| | `center_x_mm` | `float` | `50.0` | mm | Spatial centroid $X$ position |
| | `center_y_mm` | `float` | `35.0` | mm | Spatial centroid $Y$ position |
| | `orientation_deg`| `float` | `0.0` | deg | In-plane rotation angle for non-circular inclusions |
| **`geometry.weld`** | `enabled` | `bool` | `false` | - | Toggle weld bead and heat-affected-zone (HAZ) subdomains |
| | `weld_width_mm` | `float` | `12.0` | mm | Width of weld centerline bead |
| | `haz_width_mm` | `float` | `6.0` | mm | Width of adjacent heat-affected zone |
| **`contact_resistance`**| `enabled` | `bool` | `false` | - | Model imperfect interface thermal barrier |
| | `h_contact_w_m2k`| `float` | `5000.0` | $\text{W}/(\text{m}^2\cdot\text{K})$ | Interface thermal contact conductance |
| **`mesh_refinement`** | `adaptive_tensor`| `bool` | `true` | - | Non-uniform spatial grading concentrated at defect core |
| | `target_elements_across_defect` | `int` | `10` | elements | Elements resolving defect diameter ($8-12$) |
| | `target_elements_cover_layer` | `int` | `5` | elements | Elements through shallow cover depth ($4-6$) |
| **`excitation`** | `type` | `str` | `"lfmt_chirp"` | - | Excitation modality (`lfmt_chirp`, `flash`, `step`) |
| | `freq_start_hz` | `float` | `0.01` | Hz | Chirp modulation starting frequency |
| | `freq_end_hz` | `float` | `0.5` | Hz | Chirp modulation ending frequency |
| | `chirp_duration_s` | `float` | `10.0` | s | Duration of active heating chirp |
| | `peak_flux_w_m2`| `float` | `2000.0` | $\text{W}/\text{m}^2$ | Peak absorbed thermal heat flux |
| **`heating_profile`** | `profile_type` | `str` | `"uniform"` | - | Spatial heating flux profile (`uniform`, `gaussian`, `linear_gradient`) |
| | `gaussian_sigma_mm` | `float` | `40.0` | mm | Beam spread parameter for Gaussian lamps |
| **`camera`** | `model_tier` | `str` | `"research_grade"`| - | Camera hardware tier (`research_grade`, `industrial`, `low_cost`) |
| | `netd_mK` | `float` | `25.0` | mK | Noise Equivalent Temperature Difference |
| | `psf_sigma_px` | `float` | `0.5` | px | Optical Point Spread Function spatial blur standard deviation |
| | `adc_bits` | `int` | `14` | bits | Radiometric Analog-to-Digital Converter bit depth |
| | `fpn_factor` | `float` | `0.002` | - | Spatial Fixed-Pattern Noise non-uniformity standard deviation |
| | `emissivity_model` | `str`| `"radiance_planck_v2"` | - | Radiance conversion model (`radiance_planck_v2`, `simplified_kelvin_v1`) |

---

## 2. Configuration Files in Repository

- `configs/research_v2.yaml`: High-fidelity canonical configuration with adaptive mesh grading, realistic camera physics, and radiance-level emissivity.
- `configs/research_v2_split.yaml`: Parameter sweep split definition for the complete multi-depth multi-diameter design matrix.
- `configs/default.yaml`: Preserved `conference-v1.0` benchmark baseline configuration.
- `configs/quick.yaml`: Rapid test configuration for fast CI integration and developer sanity checks.

