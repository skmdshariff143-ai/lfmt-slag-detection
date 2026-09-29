# Improvement-tier verification

## Tier 1 — complete

- `python scripts/analyze_detection_surface.py`: 625 surface cells, 300 paired
  tests; all nine frozen SHA-256 hashes unchanged.
- `python scripts/trace_clean_detection.py`: 150 method/condition traces across
  all 25 geometries. Clean morphology survivors PCT=0, RPT=4, SPCT=2, all with
  zero GT overlap.
- `python -m pytest -v -p no:cacheprovider`: **98 passed, 0 failed**, six warnings,
  489.90 seconds. Full log: `tier1_pytest_verified.log` (local, ignored by Git).
- Original full-suite attempt: 97 passed, one MATLAB serialization failure;
  fixed with a numeric-result Engine wrapper. MATLAB requires execution outside
  the Codex sandbox on this host.

Frozen inputs are enumerated and hashed in `analysis_manifest.json`. Historical
seed-labelled scores are identical within every noisy method/geometry/condition
group; run-level inferential tests must not be treated as independent evidence.

## Tier 2 — complete

Five focused tests pass. Training completed on ten synthetic training geometries
and three held-out validation geometries, with clean/30/20 dB AWGN variants.
Balanced loss decreased from 0.668432 to 0.144047.

- `python scripts/run_conference_study.py --conference --config configs/conference_v2_experimental.yaml --extended-model results/conference/analysis/tier2/temporal_pixel_v1.json --outdir results/conference/analysis/tier2/benchmark_v2_2`:
  6,448 evaluations plus sensitivity completed; plotting failed due to missing
  Tcl/Tk. Batch backend was changed to Agg.
- `python scripts/finalize_extended_results.py`: 12 figures and recovery manifest
  saved, raw CSV SHA256 unchanged. End-to-end runtime explicitly unavailable.
- `python scripts/validate_extended_results.py results/conference/analysis/tier2/benchmark_v2_2`:
  passed, 806 paired inputs, eight methods, all frozen hashes unchanged.
- `python -m pytest -v -p no:cacheprovider --basetemp=$tierTemp`: **103 passed,
  0 failed**, six warnings, 3528.26 seconds. `$tierTemp` was a newly generated
  unique path under the system temporary directory to avoid a pre-existing ACL
  failure. Full log: `tier2/pytest_verified.log` (local).
- After the plotting repair, `python -m pytest -v -p no:cacheprovider tests/test_advanced_processing.py tests/test_processing.py tests/test_integration.py`:
  **14 passed, 0 failed**.

Temporal Pixel Net detection is 47.1%, but 29/31 healthy inputs are false alarms.
This is not a calibrated performance improvement. No Tier 3 work preceded this
checkpoint.

## Tier 3 — complete

- `python scripts/verify_small_defect_physics.py`: nine FEM/FDM pairs completed
  on registered camera coordinates; configurations/source hashes saved.
- `python scripts/report_small_defect_physics.py`: zero occupied FDM slag cells
  for baseline D4 cases; refined D4 represented-volume errors 128.79% and 71.59%.
- Shallow refined D4 Celsius-normalized L2=0.3196% and temperature-rise L2=3.2365%.
  These meshes do not validate D4 detectability.
- `python -m pytest -v -p no:cacheprovider --basetemp=$tierTemp`: **103 passed,
  0 failed**, six warnings, 640.57 seconds; unique fresh temporary directory,
  outside sandbox for MATLAB. Log: `tier3/pytest.log` (local).
- `data/experimental/README.md` specifies missing real LFMT slag data. Installed
  measured flash data is explicitly distinguished from LFMT physical validation.

## Tier 4 — incomplete, blocked; Tiers 5 and 6 not started

Implemented: incremental strict-mypy CI command, versioned dataset/source golden
contract with immutable historical entries, exact 97-package container lock,
Dockerfile and container CI canary, optional local MLflow study lifecycle and
real-client test. These are pending verification where noted below.

- `python scripts/verify_container_benchmark.py`: **16 method/case comparisons
  passed locally**, independently recomputing clean D4/z0.2 and healthy inputs
  for all eight methods. This is not container execution or a full-study replay.
- `python -m pytest tests/test_dataset_contract.py -v -p no:cacheprovider`:
  **2 passed, 0 failed**.
- `python scripts/validate_extended_results.py results/conference/analysis/tier2/benchmark_v2_2`:
  **6,448 records, eight methods, 806 paired inputs validated**; all nine original
  frozen-file SHA-256 hashes unchanged.
- First full `python -m pytest -v -p no:cacheprovider --basetemp=$tierTemp`:
  **104 passed, 1 failed, 1 skipped**, 699.62 seconds. MATLAB multi-defect startup
  failed with `License Error: Licensing shutdown: Invalid message - buffer too
  small 0 < 8`. Local log: `tier4/pytest.log`.
- `python -m pytest tests/test_matlab_backend.py -v -p no:cacheprovider --basetemp=$tierTemp`:
  **4 passed**, 78.48 seconds. Local log: `tier4/matlab_retry.log`.
- Final full `python -m pytest -v -p no:cacheprovider --basetemp=$tierTemp`:
  **104 passed, 1 failed, 1 skipped**, reported elapsed 14,760.07 seconds.
  `test_start_simulation_and_get_result` failed during MATLAB startup with
  `License Error: Licensing shutdown: invalid map<K, T> key`. MLflow lifecycle
  skipped because its optional package was unavailable. Local log:
  `tier4/pytest_final.log`. Every full-run temporary directory was fresh and the
  commands ran outside the sandbox for MATLAB. No test was weakened or hidden.
- `python -m mypy --strict src/lfmt/advanced_processing.py src/lfmt/ml src/lfmt/experiment_tracking.py`:
  **blocked**, `No module named mypy`. Compiled and smaller portable wheel
  installation attempts failed after network timeouts and WinError 32; a ranged
  download fallback failed with connection reset. No strict-pass claim.
- `python -m pip install --timeout 15 --retries 0 --resume-retries 0 mlflow-skinny==3.16.1`:
  **failed**, download timeout/temporary-file sharing error. No real MLflow run
  has been verified. Dependency dry-run plan saved in `tier4/dependency_plan.json`.
- `docker build --tag lfmt-benchmark:tier4 .`: **blocked**, `docker` is not
  recognized. No Docker runtime or WSL distribution is installed. The Linux
  dependency-resolution attempt also timed out. Docker build and in-container
  benchmark reproduction are unverified.

Required to resume: Docker-enabled execution environment, working package
downloads for mypy/MLflow, and reliable MATLAB licensing. No heavy package was
installed, no frozen data was modified, and no Git history or external publishing
action was performed. Tier 4 is intentionally not marked complete.
