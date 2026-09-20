"""Unit tests for material properties and validation."""

import pytest
import math
from lfmt.materials import Material, MATERIAL_DATABASE, get_material


def test_material_creation_valid():
    mat = Material(
        name="Test Alloy",
        thermal_conductivity=50.0,
        density=7800.0,
        specific_heat=500.0,
    )
    expected_diff = 50.0 / (7800.0 * 500.0)
    expected_eff = math.sqrt(50.0 * 7800.0 * 500.0)
    assert math.isclose(mat.thermal_diffusivity, expected_diff, rel_tol=1e-6)
    assert math.isclose(mat.thermal_effusivity, expected_eff, rel_tol=1e-6)


def test_material_validation_invalid_values():
    with pytest.raises(ValueError, match="Thermal conductivity must be positive"):
        Material(name="Bad K", thermal_conductivity=-5.0, density=7000.0, specific_heat=500.0)

    with pytest.raises(ValueError, match="Density must be positive"):
        Material(name="Bad Rho", thermal_conductivity=50.0, density=0.0, specific_heat=500.0)

    with pytest.raises(ValueError, match="Specific heat must be positive"):
        Material(name="Bad Cp", thermal_conductivity=50.0, density=7000.0, specific_heat=-10.0)


def test_database_retrieval():
    steel = get_material("mild_steel")
    assert steel.name == "Mild Steel (AISI 1018)"
    assert steel.thermal_conductivity == 51.9
    assert steel.density == 7850.0
    assert steel.specific_heat == 486.0
    assert not steel.is_placeholder

    slag = get_material("slag")
    assert "Slag" in slag.name
    assert slag.thermal_conductivity == 1.20
    assert slag.density == 2800.0
    assert slag.specific_heat == 850.0

    placeholder = get_material("slag_placeholder_variant")
    assert placeholder.is_placeholder

    with pytest.raises(KeyError, match="not found"):
        get_material("non_existent_unobtainium")
