# MATLAB 3-D Conservative FDM Transient Thermal Simulation Backend (`MATLAB_FDM`)

**Branch:** `scientific-hardening-v3`  
**Discretization:** 3-D Conservative Finite Difference with Harmonic Mean Interface Conductivities  
**Time Integration:** Implicit Backward Euler (Unconditionally Stable)

---

## Structure

- `+lfmt/`: Modular library containing grid generation, excitation, material assignment, sparse matrix assembly, solver, and surface interpolation.
- `run_lfmt_simulation.m`: Direct MATLAB simulation entry point.
- `run_lfmt_from_json.m`: CLI / batch entry point consuming JSON configs.
- `tests/`: Complete unit testing suite using `matlab.unittest`.
- `examples/`: Standalone runnable example scripts (healthy, shallow slag, deep slag, multi-slag).

---

## Running Unit Tests

```matlab
results = runtests('matlab/tests');
assertSuccess(results);
```
