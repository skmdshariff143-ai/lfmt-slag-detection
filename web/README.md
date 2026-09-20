# LFMT Slag Detection — Conference Web Portal & Presentation Engine

Interactive, publication-grade Next.js web application for presenting and exploring the **Linear Frequency-Modulated Infrared Thermography (LFMT)** 3-D FEM simulation benchmark dataset for subsurface slag inclusion detection in mild steel.

---

## 🌟 Overview & Features

- **No Live Simulation at Runtime:** Operates as a fast, zero-latency presentation portal reading frozen, audited JSON and image manifests generated from the 4,030-evaluation Python FEM benchmark suite.
- **Conference Presentation Mode (`/conference`):** Fullscreen, projector-optimized live demo dashboard with keyboard shortcuts, scenario presets, metric comparative overlays, and high-contrast styling.
- **Single-Case Defect Explorer (`/explorer`):** Multi-defect geometry selector with side-by-side post-processing maps and metric tables across Clean, 30 dB, 25 dB, and 20 dB noise scenarios.
- **Interactive Animated Scrubber (`/thermograms`):** Play/pause scrubber through 10-second thermal diffusion frame sequences with live temperature telemetry HUD.
- **Rigorous Mathematical & Material Documentation (`/methodology`, `/materials`, `/validation`):** KaTeX formulas for chirp heat equation, matched filtering, SVD/PCA, phase reconstruction, and thermophysical property tables.
- **Audience QR Portal (`/qr`):** Scannable high-contrast QR codes for projecting on conference screens.

---

## 🛠️ Technology Stack

- **Framework:** Next.js 14 (App Router)
- **Language:** TypeScript 5
- **Styling:** Tailwind CSS (Dark Navy & Slate Research Instrument Theme)
- **Visualizations & Charts:** Recharts
- **Mathematical Typography:** KaTeX
- **Icons:** Lucide React
- **Deployment Platform:** Vercel

---

## 🚀 Getting Started

### Prerequisites

- Node.js `v18.17.0` or higher (Node 20 / 22 recommended)
- npm `v9+`

### Installation

```bash
# Navigate to the web directory
cd web

# Install dependencies
npm install
```

### Local Development

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Build & Verification

```bash
# Type check
npm run typecheck

# Lint
npm run lint

# Production build
npm run build

# Start production server locally
npm start
```

---

## ☁️ Vercel Deployment Guide

Deploying this application to **Vercel** is instantaneous and requires no backend server or environment variables:

1. Push your changes to GitHub: `git push origin main`.
2. In the [Vercel Dashboard](https://vercel.com):
   - Click **Add New Project** → **Import Git Repository**.
   - Select `lfmt-slag-detection`.
   - **Important:** Set the **Root Directory** to `web`.
   - The Framework Preset will automatically detect **Next.js**.
3. Click **Deploy**.
4. The deployment will complete in under 60 seconds.

---

## 📂 Project Structure

```
web/
├── public/
│   ├── cases/            # Pre-rendered single-case JSONs (metrics & metadata)
│   ├── data/             # Frozen benchmark JSON summaries (methods, depths, noise, etc.)
│   ├── figures/          # Conference benchmark figures
│   └── thermograms/      # Pre-rendered WebP/PNG thermogram frames & 6-method maps
├── src/
│   ├── app/
│   │   ├── page.tsx          # Home page (Executive Summary & Key Metrics)
│   │   ├── conference/       # Fullscreen Conference Presentation Mode
│   │   ├── results/          # Method, Depth, Diameter, and Noise Results
│   │   ├── sensitivity/      # Parameter Sensitivity & Thermal Contrast
│   │   ├── validation/       # FEM vs FDM Cross-Validation & Convergence
│   │   ├── methodology/      # Mathematical Foundations & Equations (KaTeX)
│   │   ├── materials/        # Steel & Slag Thermophysical Properties
│   │   ├── explorer/         # Single-Case Defect Inspector
│   │   ├── thermograms/      # Virtual IR Camera Animated Scrubber
│   │   ├── about/            # Capstone Background & Software Citation
│   │   └── qr/               # Conference QR Code Access
│   ├── components/
│   │   ├── charts/           # Recharts Visualizations (Depth, Diameter, Noise, etc.)
│   │   ├── KaTeXMath.tsx     # LaTeX Equation Renderer
│   │   ├── Navbar.tsx        # Responsive Research Portal Header
│   │   ├── Footer.tsx        # Portal Footer & Citation
│   │   └── ProvenanceBanner.tsx # Data Provenance & Verification Badge
│   ├── lib/
│   │   └── data.ts           # Type-safe static data loaders & metric formatters
│   └── types/
│       └── research.ts       # TypeScript schemas for benchmark records
├── package.json
├── tailwind.config.js
└── tsconfig.json
```

---

## 🔒 Scientific Data Provenance

All data consumed by this web application is statically compiled from the frozen Python research benchmark:
- Benchmark records: `results/conference/final/conference_benchmark_all_evaluations.csv`
- Total evaluations: **4,030**
- Deterministic random seeds: `[42, 123, 456, 789, 101112, 131415, 161718, 192021, 222324, 252627]`
- FEM Solver: 3-D transient Galerkin FEM (`scikit-fem`)
- FDM Solver: 3-D explicit finite difference solver with CFL stability check
