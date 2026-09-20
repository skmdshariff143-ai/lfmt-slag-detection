# LFMT Synthetic Thermogram Dataset Repository

## Organization
- `data/generated/`: Standardized synthetic thermogram cases generated via `scripts/generate_dataset.py`.
- `data/cache/`: Deterministic SHA-256 simulation caches to accelerate sweeps and dashboard interactions.

## Format
Each test case folder (`case_XXXX/`) contains:
1. `thermograms.npz`: Shape `(N_frames, H, W)` in Kelvin (`float32`).
2. `ground_truth_mask.npy`: Shape `(H, W)` boolean mask (`uint8`).
3. `metadata.json`: Geometric, physical, and camera metadata.
