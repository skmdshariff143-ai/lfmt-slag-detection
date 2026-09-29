# Tier 4 reproducibility controls — checkpoint pending

The Docker build and container execution have **not** been verified on this
Windows host: Docker is absent and WSL has no installed distribution. Do not
interpret the added CI job or Dockerfile as successful build evidence.

## Incremental strict typing

CI runs `python -m mypy --strict src/lfmt/advanced_processing.py src/lfmt/ml
src/lfmt/experiment_tracking.py`. These new scientific and tracking modules form
the initial strict boundary. The legacy solver/application tree is not claimed
to be fully strict. No blanket type-error ignores have been added. Local checker
installation failed: both the compiled and portable wheels timed out and pip
reported a temporary-file sharing error. A SHA-256-checked ranged-download
attempt also failed with a remote connection reset. Thus **strict typing has not
yet been verified**; CI is configured to perform it, not claimed to pass.

## Golden contract

`tests/golden/dataset_contracts.json` records canonical-LF SHA-256 hashes of
`web/public/data/dataset-lock.json`, all nine frozen files, numerical Python
sources, YAML configurations, the study runner, and the container dependency
lock. Canonical LF avoids false changes caused by Git checkout line endings.
The initial entry binds the existing audited dataset to the reviewed working
tree; it does not assert that current code recreates historical results.

Changes fail `tests/test_dataset_contract.py` unless the dataset lock has an
explicit new version and a new contract is appended using
`python scripts/dataset_contract.py`. Review and recompute affected results into
a new versioned output directory before doing that. Historical contracts are
compared against the PR base/push predecessor in CI and cannot be replaced.
This is deliberately conservative: even a numerical-source refactor requires
review. Hashing is not a substitute for numerical reproduction.

## Container

`requirements-container.in` lists exact direct versions; the lock lists the
complete 97-package metadata dependency closure for Linux/Python 3.13. It was
constructed from installed distribution metadata and the saved pip resolution
plan. Linux wheel availability/build verification remain pending after a
package-host timeout. The lock retains the environment's prerelease Pydantic
version explicitly; it must not be described as a validated portable lock yet.

The image pins Python 3.13.13, scikit-fem 12.0.2 and SciPy 1.18.0. SciPy's
[vendored SuperLU header](https://raw.githubusercontent.com/scipy/scipy/v1.18.0/scipy/sparse/linalg/_dsolve/SuperLU/SRC/slu_util.h)
declares SuperLU 7.0.1; the binary SciPy wheel supplies that solver, not a separate
system SuperLU installation. All Python dependencies use exact versions, but
the base-image tag is not digest-pinned and wheel hashes are not yet locked.

```sh
docker build --tag lfmt-benchmark:tier4 .
docker run --rm lfmt-benchmark:tier4
docker run --rm lfmt-benchmark:tier4 python -m pytest tests/test_dataset_contract.py -v
```

The default command independently simulates clean D=4 mm/z=0.2 mm and healthy
cases, processes all eight methods, and compares detection, IoU and CNR against
the saved Tier 2 results (relative tolerance 1e-6, absolute 1e-8). It passed all
16 method/case comparisons on the local Windows environment. This is a compact
numerical canary, not a replay of all 6,448 records or the historical frozen run.

## Local experiment tracking

Install `.[tracking]`, then append `--tracking-dir <local-directory>` to
`scripts/run_conference_study.py`. MLflow uses a local SQLite metadata database
and local artifact directory; no server is needed. Config hash, config file,
method detection/IoU/healthy false-alarm metrics, summaries and manifest are
recorded. Exceptions mark a run FAILED and propagate. A missing optional MLflow
installation fails explicitly when tracking is requested. The local installation
attempt timed out with the same temporary-file sharing error, so **MLflow runtime
verification is still blocked**.

The real-client lifecycle test checks success, failure, metrics and artifacts;
it is explicitly skipped when the optional dependency is unavailable. CI
installs the tracking extra. Package download sizes verified before installation:
mypy 1.19.1 Windows wheel 10,135,510 bytes; mlflow-skinny 3.16.1 wheel 3,797,284
bytes; every other newly selected package was below 1.1 MB. Existing SQLAlchemy
2.0.36 and Alembic 1.14.0 provide the local database backend.
