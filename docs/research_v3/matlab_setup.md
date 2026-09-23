# MATLAB Integration & Setup Guide (Research V3)

## 1. Overview
The LFMT research platform features a dedicated **3-D Transient Conservative Finite-Difference Method (FDM)** simulation backend written in pure, high-performance MATLAB.

- **Solver Core**: `matlab/sim/lfmt_simulate_fdm.m` (3-D conservative flux with harmonic mean interface thermal conductivities, vectorized Laplacian stencils, automated Courant stability sub-stepping, and Robin boundary conditions).
- **Backend Bridge**: `src/lfmt/matlab/backend.py` (`MatlabSimulationBackend`).
- **Detected Environment**: MATLAB R2026a (Update 4).
- **Connection Modalities**:
  1. **Primary**: `matlab.engine` Python SDK (`import matlab.engine`).
  2. **Fallback**: Headless batch execution (`matlab -batch`).

---

## 2. Terminology & Mathematical Rigor
> [!IMPORTANT]
> - The MATLAB backend is strictly designated **`MATLAB_FDM`** (3-D Conservative Finite Difference Method).
> - It is **NOT** a finite-element model (FEM). The genuine 3-D weak variational finite-element solver is provided by the Python `scikit-fem` backend (`FEMBackend`).
> - Live MATLAB execution runs on a local workstation or dedicated compute node with MATLAB installed. It cannot run inside serverless edge runtimes (e.g., Vercel).

---

## 3. Local Installation & Configuration

### Step 1: Verify MATLAB Executable
Ensure MATLAB is accessible on your system path or set via environment variable:
```bash
# Optional explicit override (e.g., on Windows)
set LFMT_MATLAB_EXECUTABLE=E:\MATLAB\bin\matlab.exe
```

### Step 2: Install MATLAB Engine for Python (Recommended)
From an elevated command prompt / terminal inside your Python virtual environment:
```bash
# Locate MATLAB root extern directory
cd "E:\MATLAB\extern\engines\python"
python -m pip install .
```

### Step 3: Run Connection Health Check
Run the Python capability audit:
```bash
python -c "from lfmt.matlab.environment import detect_matlab_environment; print(detect_matlab_environment())"
```

Expected output:
```json
{
  "installed": true,
  "release": "R2026a",
  "engine_available": true,
  "cli_available": true,
  "pde_toolbox_installed": false,
  "preferred_solver": "MATLAB_FDM"
}
```

---

## 4. Running MATLAB Unit & Regression Tests
Run the standalone MATLAB test suite:
```bash
matlab -batch "addpath('matlab'); results=runtests('matlab/tests'); assertSuccess(results)"
```

Run Python-MATLAB integration tests:
```bash
pytest -m matlab -v
```

---

## 5. Live Demonstration Architecture
To launch the full local end-to-end stack (Next.js frontend + FastAPI backend + MATLAB Engine):
```powershell
powershell -ExecutionPolicy Bypass -File scripts/demo/start_local_demo.ps1
```
- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`
- Simulation Lab: `http://localhost:3000/simulate`
