"""
Thermophysical Material Properties Database for LFMT Simulation.

Stores verified and placeholder physical properties with validation,
derived property calculation (thermal diffusivity, thermal effusivity),
and metadata citations.
"""

from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass(frozen=True)
class Material:
    """
    Thermophysical properties of a solid material.

    Attributes:
        name: Common or standard name of the material.
        thermal_conductivity: Thermal conductivity k in W/(m·K). Must be > 0.
        density: Mass density rho in kg/m^3. Must be > 0.
        specific_heat: Specific heat capacity Cp in J/(kg·K). Must be > 0.
        is_placeholder: Flag indicating if the value is an unverified placeholder.
        reference: Citation or literature source.
        notes: Additional scientific or metallurgical notes.
    """
    name: str
    thermal_conductivity: float  # k [W/(m·K)]
    density: float               # rho [kg/m^3]
    specific_heat: float         # Cp [J/(kg·K)]
    is_placeholder: bool = False
    reference: str = "Unspecified"
    notes: str = ""

    def __post_init__(self) -> None:
        """Validate physical correctness."""
        if not self.name or not isinstance(self.name, str):
            raise ValueError("Material name must be a non-empty string.")
        if self.thermal_conductivity <= 0:
            raise ValueError(f"Thermal conductivity must be positive, got {self.thermal_conductivity} W/(m·K).")
        if self.density <= 0:
            raise ValueError(f"Density must be positive, got {self.density} kg/m^3.")
        if self.specific_heat <= 0:
            raise ValueError(f"Specific heat must be positive, got {self.specific_heat} J/(kg·K).")

    @property
    def thermal_diffusivity(self) -> float:
        r"""
        Calculate thermal diffusivity \alpha = k / (\rho \cdot C_p) [m^2/s].
        Represents rate of heat transfer through the material.
        """
        return self.thermal_conductivity / (self.density * self.specific_heat)

    @property
    def thermal_effusivity(self) -> float:
        r"""
        Calculate thermal effusivity e = \sqrt{k \cdot \rho \cdot C_p} [W·s^{1/2}/(m^2·K)].
        Measures the material's ability to exchange thermal energy with its surroundings.
        """
        return math.sqrt(self.thermal_conductivity * self.density * self.specific_heat)

    def to_dict(self) -> dict:
        """Serialize material properties with derived quantities."""
        return {
            "name": self.name,
            "thermal_conductivity_W_mK": self.thermal_conductivity,
            "density_kg_m3": self.density,
            "specific_heat_J_kgK": self.specific_heat,
            "thermal_diffusivity_m2_s": self.thermal_diffusivity,
            "thermal_effusivity_W_s05_m2K": self.thermal_effusivity,
            "is_placeholder": self.is_placeholder,
            "reference": self.reference,
            "notes": self.notes,
        }


# Structured scientific material database
MATERIAL_DATABASE: Dict[str, Material] = {
    "mild_steel": Material(
        name="Mild Steel (AISI 1018)",
        thermal_conductivity=51.9,     # W/(m·K)
        density=7850.0,                # kg/m^3
        specific_heat=486.0,           # J/(kg·K)
        is_placeholder=False,
        reference="Incropera, F.P., & DeWitt, D.P., Fundamentals of Heat and Mass Transfer (7th Ed.)",
        notes="Standard structural low-carbon steel matrix for NDT weldment testing."
    ),
    "slag": Material(
        name="Welding Slag (Silicate / Flux Residue)",
        thermal_conductivity=1.20,     # W/(m·K) (typical range 0.8 - 2.0 W/(m·K))
        density=2800.0,                # kg/m^3 (typical range 2500 - 3200 kg/m^3)
        specific_heat=850.0,           # J/(kg·K) (typical range 800 - 1100 J/(kg·K))
        is_placeholder=False,
        reference="Mills, K.C., Structure and Properties of Slags (1993); ASM Handbook Vol. 6 (Welding)",
        notes="Calcium-silicate / alumino-silicate entrapment typical in SMAW/FCAW weld defects."
    ),
    "air_cavity": Material(
        name="Air / Delamination Void",
        thermal_conductivity=0.026,    # W/(m·K) at 300 K
        density=1.161,                 # kg/m^3 at 300 K, 1 atm
        specific_heat=1007.0,          # J/(kg·K)
        is_placeholder=False,
        reference="NIST Standard Reference Database 69 (NIST Chemistry WebBook)",
        notes="Gaseous void / lack of fusion porosity."
    ),
    "stainless_steel_304": Material(
        name="Stainless Steel (AISI 304)",
        thermal_conductivity=14.9,     # W/(m·K)
        density=7900.0,                # kg/m^3
        specific_heat=477.0,           # J/(kg·K)
        is_placeholder=False,
        reference="Incropera & DeWitt (7th Ed.)",
        notes="Austenitic stainless steel comparison baseline."
    ),
    "slag_placeholder_variant": Material(
        name="Slag High-TiO2 Flux (Experimental Estimate)",
        thermal_conductivity=1.45,
        density=2950.0,
        specific_heat=880.0,
        is_placeholder=True,
        reference="[PLACEHOLDER: Pending experimental flash-diffusivity verification]",
        notes="Placeholder dataset for titanium-oxide enriched rutile flux slag."
    ),
}


def get_material(identifier: str) -> Material:
    """
    Retrieve material by key name or case-insensitive search.

    Args:
        identifier: Key name (e.g. 'mild_steel', 'slag') or full name.

    Returns:
        Material dataclass instance.

    Raises:
        KeyError: If material is not found in database.
    """
    key = identifier.strip().lower().replace(" ", "_").replace("-", "_")
    if key in MATERIAL_DATABASE:
        return MATERIAL_DATABASE[key]

    for k, mat in MATERIAL_DATABASE.items():
        if identifier.lower() in mat.name.lower() or k == key:
            return mat

    available = ", ".join(list(MATERIAL_DATABASE.keys()))
    raise KeyError(f"Material '{identifier}' not found. Available materials: {available}")
