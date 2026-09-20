# MATLAB Academic Comparison Suite for LFMT Slag Detection

This directory contains pure MATLAB implementations of the Linear Frequency-Modulated Thermography (LFMT) computational pipeline for academic benchmarking.

## Requirements
- MATLAB R2021a or newer
- **Signal Processing Toolbox** (for `xcorr`, `chirp` waveforms)
- **Image Processing Toolbox** (for `viscircles`, `imagesc` spatial operations)
- **Statistics and Machine Learning Toolbox** (for `svd`, PCA analysis)

## Structure
```
matlab/
├── main.m                         # Master execution script
├── simulation/
│   └── lfmt_simulate_3d_heat.m    # 3D transient conduction forward solver
├── processing/
│   ├── lfmt_matched_filter.m      # Cross-correlation pulse compression
│   ├── lfmt_pct.m                 # SVD Principal Component Thermography
│   └── lfmt_rpt.m                 # Gaussian Random Projection Technique
└── visualization/
    └── lfmt_plot_comparison.m     # High-resolution multi-panel figures
```

## Running the Academic Benchmark
Open MATLAB, set current directory to `matlab/`, and execute:
```matlab
main
```
