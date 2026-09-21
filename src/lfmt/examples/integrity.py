"""
Deterministic SHA256 integrity verification for the verified example data library.
"""

from __future__ import annotations
import hashlib
from pathlib import Path
from typing import List, Tuple, Dict, Any


def compute_sha256(filepath: Path) -> str:
    """Compute deterministic SHA256 hex digest for a file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def verify_example_integrity(example_dir: str | Path) -> Tuple[bool, List[str]]:
    """
    Verify all files in an example directory against its sha256.txt manifest.
    Returns (is_valid, error_messages).
    """
    p_dir = Path(example_dir)
    sha_file = p_dir / "sha256.txt"
    if not sha_file.exists():
        return False, [f"Integrity manifest sha256.txt missing in {p_dir}"]

    errors = []
    lines = sha_file.read_text(encoding="utf-8").splitlines()
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(maxsplit=1)
        if len(parts) != 2:
            continue
        expected_sha, fname = parts[0], parts[1]
        target_f = p_dir / fname
        if not target_f.exists():
            errors.append(f"Required file '{fname}' is missing in {p_dir.name}")
            continue
        actual_sha = compute_sha256(target_f)
        if actual_sha.lower() != expected_sha.lower():
            errors.append(
                f"Checksum mismatch for '{fname}': expected {expected_sha[:12]}..., got {actual_sha[:12]}..."
            )

    return (len(errors) == 0), errors
