# Dataset Schema & NPZ Format Specification

## Directory Structure
```
data/
├── README.md
└── generated/
    ├── case_0001/
    │   ├── thermograms.npz          # Compressed 3D thermal sequence
    │   ├── metadata.json            # Configuration and ground truth metadata
    │   └── ground_truth_mask.npy    # 2D ground truth binary mask
    └── case_0002/
        ...
```

## NPZ File Structure (`thermograms.npz`)
- `thermograms`: `float32` array with shape `(N_frames, H, W)` containing absolute surface temperatures $T(t, y, x)$ in Kelvin.
- `time_vector`: `float32` array with shape `(N_frames,)` containing time points in seconds $[0, T_{total}]$.

## Metadata Structure (`metadata.json`)
```json
{
  "case_id": "case_0001",
  "tensor_shape": [61, 64, 64],
  "time_duration_s": 12.0,
  "fps": 10.0,
  "resolution": [64, 64],
  "ground_truth": {
    "center_x_mm": 50.0,
    "center_y_mm": 35.0,
    "depth_mm": 0.6,
    "diameter_mm": 8.0,
    "thickness_mm": 0.5,
    "material_name": "Welding Slag (Silicate / Flux Residue)",
    "area_mm2": 50.265,
    "volume_mm3": 25.133,
    "has_defect": true
  }
}
```

## Binary Mask (`ground_truth_mask.npy`)
- `uint8` 2D array of shape `(H, W)` where `1` represents inclusion defect projection and `0` represents sound steel matrix.
