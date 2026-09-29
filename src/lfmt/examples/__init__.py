"""
Scientific Example Data Library Service for Research V3.
"""

from lfmt.examples.registry import ExampleRegistry
from lfmt.examples.loader import load_example, LoadedExample
from lfmt.examples.integrity import verify_example_integrity, compute_sha256

__all__ = [
    "ExampleRegistry",
    "load_example",
    "LoadedExample",
    "verify_example_integrity",
    "compute_sha256",
]
