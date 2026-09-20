"""
LFMT Slag Detection Package
Linear Frequency-Modulated Infrared Thermography for Subsurface Slag Inclusion Detection in Mild Steel.
"""

__version__ = "0.1.0"
__author__ = "Research Team"

from lfmt.materials import Material, MATERIAL_DATABASE, get_material
from lfmt.excitation import LFMTExcitation, generate_lfmt_waveform
from lfmt.config import LFMTConfig, load_config

__all__ = [
    "__version__",
    "Material",
    "MATERIAL_DATABASE",
    "get_material",
    "LFMTExcitation",
    "generate_lfmt_waveform",
    "LFMTConfig",
    "load_config",
]
