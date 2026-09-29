FROM python:3.13.13-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MPLBACKEND=Agg \
    OPENBLAS_NUM_THREADS=1 \
    OMP_NUM_THREADS=1 \
    PYTHONPATH=/workspace/src
WORKDIR /workspace
COPY requirements-container.lock ./
# Binary SciPy 1.18.0 includes SuperLU 7.0.1; do not substitute system SuperLU.
RUN python -m pip install --no-cache-dir --only-binary=:all: -r requirements-container.lock
COPY . .
RUN python -m pip install --no-deps --no-build-isolation -e . \
    && python -m pip check
CMD ["python", "scripts/verify_container_benchmark.py"]
