"""Versioned golden contracts: canonical-LF hashes of data and numerical sources."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCK = ROOT / "web/public/data/dataset-lock.json"
GOLDEN = ROOT / "tests/golden/dataset_contracts.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def snapshot() -> dict[str, object]:
    numerical = [*sorted((ROOT / "src/lfmt").rglob("*.py")),
                 *sorted((ROOT / "configs").glob("*.yaml")),
                 ROOT / "scripts/run_conference_study.py",
                 ROOT / "requirements-container.lock"]
    return {
        "dataset_lock_sha256_lf": digest(LOCK),
        "numerical_sources_sha256_lf": {str(path.relative_to(ROOT)).replace("\\", "/"): digest(path) for path in numerical},
        "frozen_files_sha256_lf": {path.name: digest(path) for path in sorted((ROOT / "results/conference/final").iterdir()) if path.is_file()},
    }


def main() -> None:
    version = json.loads(LOCK.read_text(encoding="utf-8"))["dataset_version"]
    contracts = json.loads(GOLDEN.read_text(encoding="utf-8")) if GOLDEN.exists() else {"versions": {}}
    if version in contracts["versions"]:
        raise ValueError("This version already has a golden contract; explicitly bump the dataset version before adding a new contract")
    contracts["versions"][version] = snapshot()
    GOLDEN.parent.mkdir(parents=True, exist_ok=True)
    GOLDEN.write_text(json.dumps(contracts, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Added golden contract for {version}; existing versions preserved")


if __name__ == "__main__":
    main()
