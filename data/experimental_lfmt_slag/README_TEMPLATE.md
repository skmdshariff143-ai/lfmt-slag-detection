# Future Experimental LFMT Physical Slag Dataset Schema

This directory defines the standardized structure, metadata schema, and ingestion requirements for future physical LFMT thermography experiments on mild-steel weld specimens with entrapped slag inclusions.

---

## 1. Directory Structure

```text
data/experimental_lfmt_slag/
├── README.md                          # Experiment log and specimen details
├── metadata.json                      # Machine-readable experiment parameters
├── calibration/
│   ├── spatial_target.tiff           # Optical grid for mm/pixel scale factor
│   └── emissivity_reference.csv      # Contact thermocouple vs radiometer calibration
├── raw/
│   ├── sequence_chirp_01.npz          # 3D thermal sequence (N_frames, H, W) [K]
│   └── reference_chirp.csv           # Drive signal / excitation power log
└── ground_truth/
    ├── micro_ct_reconstruction.vti   # High-resolution X-ray CT volume
    └── defect_centroids_mm.json      # Verified 3D defect coordinates & depths
```

---

## 2. Standardized `metadata.json` Schema

```json
{
  "experiment_id": "LFMT-STEEL-SLAG-2026-EXP01",
  "date_utc": "YYYY-MM-DDTHH:MM:SSZ",
  "facility": "Laboratory / Welding NDT Center",
  "specimen": {
    "material": "Structural Mild Steel (e.g. S275JR / ASTM A36)",
    "dimensions_mm": [100.0, 70.0, 2.3],
    "surface_condition": "Matt black high-emissivity coating (ε = 0.95)",
    "defect_type": "Synthetic entrapment of welding slag (SiO2-MnO-FeO mixture)",
    "defect_ground_truth": [
      {
        "defect_id": "D1",
        "diameter_mm": 4.0,
        "depth_mm": 0.5,
        "centroid_xy_mm": [50.0, 35.0],
        "verification_method": "Micro-focus X-ray Computed Tomography"
      }
    ]
  },
  "excitation": {
    "type": "linear_frequency_modulated_chirp",
    "source": "Halogen lamp array / Laser diode line / Induction coil",
    "optical_power_watts": 1000.0,
    "f_start_hz": 0.01,
    "f_end_hz": 0.50,
    "duration_s": 10.0,
    "cooling_duration_s": 2.0,
    "total_duration_s": 12.0
  },
  "camera": {
    "model": "FLIR A655sc / Telops FAST-IR",
    "spectral_band_um": [7.5, 14.0],
    "spatial_resolution_px": [64, 64],
    "frame_rate_hz": 10.0,
    "netd_mk": 25.0,
    "pixel_pitch_mm": 1.09375
  },
  "processing_configuration": {
    "blind_mode": true,
    "matched_filter": {
      "enabled": true,
      "reference_chirp_file": "raw/reference_chirp.csv"
    },
    "pct": {
      "n_components": 6,
      "selection_criterion": "blind_kurtosis"
    },
    "spct": {
      "n_components": 6,
      "alpha": 0.05
    },
    "rpt": {
      "n_components": 6,
      "matrix_type": "gaussian"
    }
  }
}
```
