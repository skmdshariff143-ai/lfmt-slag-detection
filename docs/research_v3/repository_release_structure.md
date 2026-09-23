# Repository Release Structure (Research V3)

```
lfmt-slag-detection/
├── .github/
│   └── workflows/
│       └── ci.yml             # GitHub Actions CI matrix (Python 3.10-3.12 + Next.js build)
├── api/                       # FastAPI REST API Backend
│   ├── routes/                # Endpoints (/analyze, /examples, /simulate)
│   ├── schemas/               # Pydantic request/response validation schemas
│   └── main.py                # FastAPI ASGI application entrypoint
├── src/
│   └── lfmt/                  # Core Python Package
│       ├── analysis/          # Universal defect analyzer & applicability engine
│       ├── data/              # Loader for external measured & synthetic thermograms
│       ├── examples/          # Verified example library, registry, and SHA-256 integrity
│       ├── excitation/        # LFMT chirp waveform generators & temporal modulation
│       ├── materials/         # Thermophysical property database (AISI 1018, slag, etc.)
│       ├── matlab/            # MATLAB Python Engine bridge, detector, & runner
│       ├── processing/        # NDT processing (Raw, Matched Filter, PCT, SPCT, RPT)
│       └── simulation/        # 3D weak-variational FEM solver (scikit-fem)
├── matlab/                    # High-Performance MATLAB Numerical Core
│   ├── sim/                   # 3-D conservative FDM solver (lfmt_simulate_fdm.m)
│   ├── tests/                 # MATLAB unit & verification tests
│   └── utils/                 # Matrix exports and thermal physics helpers
├── ml/                        # Machine Learning Architecture
│   ├── models/                # Multi-task U-Net Lite, Spatial CNN, Physics MLP
│   └── export/                # ONNX model graph serialization & edge runtime
├── web/                       # Next.js 14 Frontend Web Portal
│   ├── public/
│   │   └── demo/              # Verified precomputed MATLAB benchmark artifact
│   ├── src/
│   │   ├── app/               # Next.js App Router (19 static/dynamic routes)
│   │   ├── components/        # Interactive heatmaps, HUDs, charts, telemetry
│   │   └── lib/               # API client (api.ts) & runtime detector (runtime.ts)
│   └── package.json           # Frontend dependencies & build scripts
├── configs/                   # Simulation & benchmark YAML configurations
├── data/
│   ├── examples/              # Verified reference thermogram library (Category A & B)
│   └── real_world_external/   # External measured benchmark schemas & previews
├── docs/                      # Comprehensive scientific & deployment documentation
│   ├── research_v2/           # Historical Research V2 reports
│   ├── research_v3/           # Research V3 architecture, MATLAB, provenance, claims
│   └── releases/              # Release notes & changelogs
├── results/                   # Audited conference results (4,030 evaluations)
├── scripts/                   # Verification, benchmark runner, audit, and demo scripts
│   └── demo/
│       └── start_local_demo.ps1 # One-click full-stack local demo launcher
├── tests/                     # Comprehensive pytest test suite (portable + MATLAB)
├── pyproject.toml             # Python packaging, dependencies, and test config
├── .gitattributes             # Git LF line-ending & binary file normalization
├── .gitignore                 # Exclusion rules for temporary/large binaries
└── .vercelignore              # Vercel serverless build isolation rules
```
