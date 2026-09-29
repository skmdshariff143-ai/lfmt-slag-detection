# Production Deployment Guide: Vercel Frontend & Local Backend

## 1. Architectural Scope & Target Topology
The platform is designed with a strict decoupled deployment topology:

```
┌─────────────────────────────────────────────────────────────┐
│                    HOSTED VERCEL PREVIEW                    │
│  - Directory: web/                                          │
│  - Runtime: Node.js 20.x / Next.js 14                       │
│  - Delivery: Static & Edge Global CDN                       │
│  - Live Backend: Offline by design                          │
│  - Simulation Mode: Verified Precomputed MATLAB Benchmark   │
└─────────────────────────────────────────────────────────────┘
                               ▲
                               │ Optional remote URL
                               │ (NEXT_PUBLIC_API_BASE_URL)
┌──────────────────────────────┴──────────────────────────────┐
│                  LOCAL WORKSTATION BACKEND                  │
│  - Runtime: Python 3.10-3.13 / FastAPI (port 8000)          │
│  - Solvers: scikit-fem (Python) + MATLAB Engine (R2026a)   │
│  - Execution: scripts/demo/start_local_demo.ps1             │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Vercel Frontend Configuration
Configure the project in the Vercel Dashboard or via project settings:

| Setting | Value | Rationale |
| :--- | :--- | :--- |
| **Root Directory** | `web` | Scopes build strictly to Next.js; prevents scanning root `pyproject.toml` |
| **Framework Preset** | `Next.js` | Uses Next.js zero-config build optimizer |
| **Node.js Version** | `20.x` | Modern LTS runtime |
| **Install Command** | `npm ci` | Clean deterministic dependency installation |
| **Build Command** | `npm run build` | Compiles 19 static/dynamic application routes |
| **Output Directory** | `default` (`.next`) | Next.js build output |

> [!WARNING]
> **Environment Variables on Vercel**:
> If no public remote FastAPI server is hosted, do **NOT** set `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000` in the Vercel dashboard. Leave `NEXT_PUBLIC_API_BASE_URL` unset. The frontend automatically detects hosted preview mode via `web/src/lib/runtime.ts` and gracefully enables the **Precomputed MATLAB Numerical Simulation** backup without throwing localhost network errors.

---

## 3. Serverless Exclusion (`.vercelignore`)
The repository includes root [`.vercelignore`](../.vercelignore) and [`web/.vercelignore`](../web/.vercelignore) files that exclude:
- Heavy scientific dependencies (PyTorch, ONNX, scikit-fem, scipy, numpy).
- MATLAB source code and binaries.
- Intermediate datasets and result CSVs.
- This ensures Vercel bundle size remains minimal (~96 kB first-load JS) and function size limits are never exceeded.

---

## 4. Local Full-Stack Launch
For live conference presentations and real-time MATLAB simulation:
```powershell
powershell -ExecutionPolicy Bypass -File scripts/demo/start_local_demo.ps1
```
This starts:
1. FastAPI on `http://localhost:8000` (connecting to local MATLAB Engine).
2. Next.js on `http://localhost:3000`.
