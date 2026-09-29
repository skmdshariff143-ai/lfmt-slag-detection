"""Fail closed on changed lock/data/numerical sources without a versioned contract."""
import json
import os
import subprocess

from scripts.dataset_contract import GOLDEN, LOCK, ROOT, snapshot


def test_dataset_lock_and_numerical_contract():
    version = json.loads(LOCK.read_text(encoding="utf-8"))["dataset_version"]
    contracts = json.loads(GOLDEN.read_text(encoding="utf-8"))["versions"]
    assert version in contracts, "New dataset version needs an explicit golden contract"
    assert snapshot() == contracts[version], (
        "Dataset lock, frozen data, dependency lock, or numerical source changed. "
        "Review/recompute results and explicitly version the dataset; do not overwrite its golden contract."
    )


def test_historical_golden_contracts_are_immutable_in_ci():
    base = os.environ.get("LFMT_GOLDEN_BASE_REF", "")
    if not base or base == "0" * 40:
        return
    subprocess.run(["git", "cat-file", "-e", base], cwd=ROOT, check=True, capture_output=True)
    previous = subprocess.run(["git", "show", f"{base}:tests/golden/dataset_contracts.json"],
                              cwd=ROOT, capture_output=True, text=True)
    if previous.returncode:
        # First introduction of this contract file has no historical entries.
        return
    old = json.loads(previous.stdout)["versions"]
    new = json.loads(GOLDEN.read_text(encoding="utf-8"))["versions"]
    for version, contract in old.items():
        assert new.get(version) == contract, f"Historical contract {version} was changed; append a new version"
