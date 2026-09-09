"""
Unit tests for strict separation of thermal inversion vs poor ventilation.
"""

from app.physics.diagnostics import calculate_inversion_indicator, calculate_accumulation_potential


def test_low_pbl_without_vertical_data_does_not_claim_inversion():
    """Requirement 2: Low PBL + low wind alone MUST NOT return inversion_detected = True."""
    inv = calculate_inversion_indicator(temp_surface_c=None, temp_upper_c=None)

    assert inv["inversion_detected"] is None
    assert inv["status"] == "vertical_data_unavailable"

    accum = calculate_accumulation_potential(speed_ms=1.0, pbl_height_m=200.0)
    assert accum["poor_ventilation"] is True
    assert accum["accumulation_potential_score"] > 0.6


def test_vertical_temp_gradient_triggers_confirmed_inversion():
    """Requirement 2: Confirmed inversion occurs ONLY when vertical temperature profile (dT/dz > 0) exists."""
    # Warm air aloft (25°C at 200m) over cold surface (18°C at ground) ->
    # Inversion
    inv = calculate_inversion_indicator(
        temp_surface_c=18.0,
        temp_upper_c=25.0,
        delta_z_m=200.0)

    assert inv["inversion_detected"] is True
    assert inv["lapse_rate_c_100m"] == 3.5  # +3.5°C per 100m
    assert inv["status"] == "calculated_from_vertical_temp_profile"
