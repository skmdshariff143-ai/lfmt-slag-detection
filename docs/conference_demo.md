# Conference Live Demo & Presentation Guide

## 1. Quick Launch
To start the live interactive dashboard:
```bash
streamlit run app/dashboard.py
```

## 2. Conference Mode Highlights
1. **Top KPI Metrics**: Instant visibility into defect geometry (Diameter, Depth, Aspect Ratio $D/z$), Top Performing Algorithm, Peak CNR, and Sub-millimeter Localization Error.
2. **Defect Isolation Multi-Panel**: Live side-by-side display of Ground Truth vs Raw Contrast, Matched Filter, PCT, SPCT, and RPT with overlaid predicted and true bounding contours.
3. **Interactive Slider Controls**: Dynamically sweep inclusion diameter ($4 - 12\text{ mm}$), depth ($0.2 - 1.0\text{ mm}$), and AWGN noise levels ($20 - 30\text{ dB}$).
4. **Deterministic Disk Caching**: Repeated interactive tests execute in $< 1.5\text{ seconds}$ thanks to SHA-256 caching.
